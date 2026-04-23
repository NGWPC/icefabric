import hashlib
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from logging import Logger
from pathlib import Path
from threading import BoundedSemaphore
from typing import Any

from fastapi import HTTPException, Request
from pyiceberg.catalog import Catalog
from rustworkx import PyDiGraph

_log = logging.getLogger(__name__)


class _GpkgAdmission:
    """Context manager returned by :meth:`GpkgLimiter.admit`.

    Enforces, in order: queue-depth admission (429 fast-fail when too many
    requests are already waiting), then semaphore acquire with timeout
    (503 if the wait exceeds ``queue_timeout_s``). Releases the semaphore
    on exit. ``release()`` is idempotent so callers streaming a response
    (e.g. FastAPI FileResponse) can free the slot early while still being
    wrapped in ``with``.
    """

    def __init__(
        self,
        limiter: "GpkgLimiter",
        *,
        logger: logging.Logger | None,
        context: str,
    ) -> None:
        self._limiter = limiter
        self._logger = logger
        self._context = context
        self._sem_held = False

    def __enter__(self) -> "_GpkgAdmission":
        lim = self._limiter
        with lim.queue_lock:
            if lim.waiting >= lim.max_queue_depth:
                current = lim.waiting
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Hydrofabric service is over capacity "
                        f"({current} requests already queued, max "
                        f"{lim.max_queue_depth}). Please retry shortly."
                    ),
                    headers={"Retry-After": "30"},
                )
            lim.waiting += 1
        start = time.monotonic()
        try:
            acquired = lim.semaphore.acquire(timeout=lim.queue_timeout_s)
        finally:
            with lim.queue_lock:
                lim.waiting -= 1
        if not acquired:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Hydrofabric service is at capacity. Please retry shortly. "
                    f"(waited {lim.queue_timeout_s:.0f}s for a slot)"
                ),
                headers={"Retry-After": "30"},
            )
        self._sem_held = True
        wait_ms = (time.monotonic() - start) * 1000
        if wait_ms > 250 and self._logger is not None:
            suffix = f" {self._context}" if self._context else ""
            self._logger.info(f"gpkg semaphore wait: {wait_ms:.0f} ms{suffix}")
        return self

    def release(self) -> None:
        """Release the semaphore slot. Idempotent; safe to call in error paths."""
        if self._sem_held:
            self._sem_held = False
            self._limiter.semaphore.release()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()


@dataclass
class GpkgLimiter:
    """Per-app concurrency + admission guard for the hydrofabric gpkg endpoint.

    ``semaphore`` caps concurrent heavy builds per worker. ``max_queue_depth``
    caps how many additional requests may be *waiting* on that semaphore
    before we shed load with a 429 instead of letting clients sit through
    ``queue_timeout_s`` of silence. ``waiting`` is the live waiter count,
    guarded by ``queue_lock``. Use :meth:`admit` from request handlers; it
    wraps the full admission protocol as a context manager.
    """

    semaphore: BoundedSemaphore
    queue_timeout_s: float
    max_queue_depth: int = 15
    queue_lock: threading.Lock = field(default_factory=threading.Lock)
    waiting: int = 0

    def admit(self, *, logger: logging.Logger | None = None, context: str = "") -> _GpkgAdmission:
        """Return a context manager that performs queue-depth + timeout admission.

        Raises ``HTTPException(429)`` if the queue is full, ``HTTPException(503)``
        if the semaphore can't be acquired within ``queue_timeout_s``. ``context``
        is appended to the ``semaphore wait`` log line when it exceeds 250ms.
        """
        return _GpkgAdmission(self, logger=logger, context=context)


@dataclass
class StreamflowData:
    """Icechunk repo + xarray Dataset for streamflow. Open once per worker."""

    dataset: Any
    repo: Any


class GpkgCache:
    """Disk-based result cache for hydrofabric gpkg responses.

    Key: sha256 of (namespace, id_type, identifier, snapshot_id). Any table
    snapshot change naturally invalidates keys. Eviction is an LRU-by-atime
    cap on file count (simpler than tracking bytes and good enough here).
    """

    def __init__(self, cache_dir: Path, max_entries: int):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        self._evict_lock = threading.Lock()

    @staticmethod
    def key(namespace: str, id_type: str, identifier: str, snapshot_id: str) -> str:
        """Build the deterministic cache key for a subset request."""
        raw = f"{namespace}:{id_type}:{identifier}:{snapshot_id}".encode()
        return hashlib.sha256(raw).hexdigest()

    def path(self, key: str) -> Path:
        """Return the on-disk path for a given cache key."""
        return self.cache_dir / f"{key}.gpkg"

    def get(self, key: str) -> Path | None:
        """Return cached path if present (and bump atime for LRU); else None."""
        p = self.path(key)
        if not p.exists():
            return None
        try:
            os.utime(p, None)  # bump atime/mtime for LRU
        except OSError:
            pass
        return p

    def commit(self, key: str, built_path: Path) -> Path:
        """Atomically install a freshly-built gpkg at the cache path.

        Caller should write to a temp path first, then call commit() to move.
        Safe under concurrent writers for the same key (last writer wins on
        identical content).
        """
        dest = self.path(key)
        os.replace(built_path, dest)
        self._evict_if_needed()
        return dest

    def _evict_if_needed(self) -> None:
        with self._evict_lock:
            files = list(self.cache_dir.glob("*.gpkg"))
            if len(files) <= self.max_entries:
                return
            files.sort(key=lambda p: p.stat().st_atime)
            for old in files[: len(files) - self.max_entries]:
                try:
                    old.unlink()
                    _log.info(f"gpkg cache evicted {old.name}")
                except OSError:
                    pass


def get_catalog(request: Request) -> Catalog:
    """Gets the pyiceberg catalog reference from the app state

    Parameters
    ----------
    request : Request
        The FastAPI request object containing the application state

    Returns
    -------
    pyiceberg.catalog.Catalog
        The loaded pyiceberg catalog instance used for querying versioned EDFS data

    Raises
    ------
    HTTPException
        If the catalog is not loaded or not available in the application state.
        Returns HTTP 500 status code with "Catalog not loaded" detail message.
    """
    # enforce that app state has catalog
    if not hasattr(request.app.state, "catalog") or request.app.state.catalog is None:
        raise HTTPException(status_code=500, detail="Catalog not loaded")

    # route request to appropriate catalog (cache/aws)
    if (
        "domain" in request.query_params
        and request.query_params["domain"] in request.app.state.cached_namespaces
    ):
        return request.app.state.cache_catalog
    else:
        return request.app.state.catalog


def get_cached_namespaces(request: Request) -> set:
    """Gets set of all cached namespaces"""
    return set(request.app.state.cached_namespaces)


# Explicitly request cache catalog
def get_cache_catalog(request: Request) -> Catalog:
    """Gets the pyiceberg catalog reference from the app state

    Parameters
    ----------
    request : Request
        The FastAPI request object containing the application state

    Returns
    -------
    pyiceberg.catalog.Catalog
        The loaded pyiceberg catalog instance used for querying versioned EDFS data

    Raises
    ------
    HTTPException
        If the catalog is not loaded or not available in the application state.
        Returns HTTP 500 status code with "Catalog not loaded" detail message.
    """
    # enforce that app state has catalog
    if not hasattr(request.app.state, "cache_catalog") or request.app.state.cache_catalog is None:
        raise HTTPException(status_code=500, detail="Catalog not loaded")

    return request.app.state.cache_catalog


def get_graphs(request: Request) -> PyDiGraph:
    """Gets the rustworkx graph objects from the app state

    Parameters
    ----------
    request : Request
        The FastAPI request object containing the application state

    Returns
    -------
    dict[str, rustworkx.PyDiGraph]
        A dictionary with all pydigraph objects

    Raises
    ------
    HTTPException
        If the catalog is not loaded or not available in the application state.
        Returns HTTP 500 status code with "Catalog not loaded" detail message.
    """
    if not hasattr(request.app.state, "network_graphs") or request.app.state.network_graphs is None:
        raise HTTPException(status_code=500, detail="network_graphs not loaded")
    return request.app.state.network_graphs


def get_gpkg_limiter(request: Request) -> GpkgLimiter:
    """Returns the per-app GpkgLimiter; 500 if not configured in lifespan."""
    limiter = getattr(request.app.state, "gpkg_limiter", None)
    if limiter is None:
        raise HTTPException(status_code=500, detail="gpkg_limiter not loaded")
    return limiter


def get_streamflow_data(request: Request) -> StreamflowData:
    """Returns the cached StreamflowData opened in lifespan."""
    data = getattr(request.app.state, "streamflow_data", None)
    if data is None:
        raise HTTPException(status_code=503, detail="streamflow_data not loaded")
    return data


def get_gpkg_cache(request: Request) -> GpkgCache | None:
    """Returns the per-app GpkgCache; None if disabled (caching skipped)."""
    return getattr(request.app.state, "gpkg_cache", None)
