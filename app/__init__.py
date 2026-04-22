from dataclasses import dataclass
from logging import Logger
from threading import BoundedSemaphore

from fastapi import HTTPException, Request
from pyiceberg.catalog import Catalog
from rustworkx import PyDiGraph


@dataclass
class GpkgLimiter:
    """Per-app concurrency guard for the hydrofabric gpkg endpoint."""

    semaphore: BoundedSemaphore
    queue_timeout_s: float


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
