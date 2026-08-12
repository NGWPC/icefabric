"""
Load test for the icefabric API.

Targets 3 commonly-used endpoints at ~100 requests/minute total, with valid
CONUS NHF identifiers. Designed to run against a locally Dockerized API with
t3.large-equivalent resource caps.

Usage
-----
    python load_test.py --base-url http://localhost:8000 --rpm 100 --duration 300
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import random
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Identifier pools (valid CONUS NHF)
# ---------------------------------------------------------------------------
# NHF CONUS VPU IDs. These are the standard National Hydrofabric VPU codes.
VPU_IDS: list[str] = [f"{i:02d}" for i in range(1, 19)]  # "01".."18"

# Known-valid NHF flowpath IDs (integers). Populated at runtime from the
# `/available` / hydrofabric responses when possible; defaults below are from
# the router's documented examples and a safe spread.
FLOWPATH_IDS: list[int] = [3490271]

# Parameter-metadata modules
MODULES: list[str] = [
    "CFE-S",
    "CFE-X",
    "LASAM",
    "LSTM",
    "Noah-OWP-Modular",
    "PET",
    "Sac-SMA",
    "SFT",
    "SMP",
    "Snow-17",
    "T-Route",
    "TopModel",
    "Topoflow-Glacier",
    "UEB",
]

# Fallback gauge IDs (USGS) — the driver will try to fetch a fresh list from
# /streamflow_observations/available at start; these are the safety net.
FALLBACK_GAGES: list[str] = [
    "01010000",
    "01031500",
    "02GC002",
    "08102730",
    "01013500",
    "01022500",
    "01030500",
    "01047000",
]


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------
@dataclass
class Sample:
    endpoint: str
    url: str
    status: int
    latency_ms: float
    error: str | None = None
    bytes: int = 0
    started_at: float = 0.0


@dataclass
class Results:
    samples: list[Sample] = field(default_factory=list)

    def add(self, s: Sample) -> None:
        self.samples.append(s)

    def summary(self) -> dict:
        by_ep: dict[str, list[Sample]] = defaultdict(list)
        for s in self.samples:
            by_ep[s.endpoint].append(s)

        out: dict = {"overall": self._stats(self.samples), "by_endpoint": {}}
        for ep, xs in by_ep.items():
            out["by_endpoint"][ep] = self._stats(xs)
        return out

    @staticmethod
    def _stats(xs: list[Sample]) -> dict:
        if not xs:
            return {"count": 0}
        lats = [s.latency_ms for s in xs]
        codes = Counter(s.status for s in xs)
        ok = sum(1 for s in xs if 200 <= s.status < 300)
        errs = sum(1 for s in xs if s.status >= 500 or s.status == 0)
        lats_sorted = sorted(lats)

        def pct(p):
            if not lats_sorted:
                return 0.0
            k = int(round((p / 100.0) * (len(lats_sorted) - 1)))
            return lats_sorted[k]

        return {
            "count": len(xs),
            "success": ok,
            "errors_5xx_or_conn": errs,
            "status_codes": dict(codes),
            "latency_ms": {
                "min": round(min(lats), 1),
                "mean": round(statistics.mean(lats), 1),
                "p50": round(pct(50), 1),
                "p95": round(pct(95), 1),
                "p99": round(pct(99), 1),
                "max": round(max(lats), 1),
            },
            "total_bytes": sum(s.bytes for s in xs),
        }


# ---------------------------------------------------------------------------
# Request builders
# ---------------------------------------------------------------------------
def build_hydrofabric_request(gages: list[str]) -> tuple[str, str]:
    """Hydrofabric NHF subset — realistic mix of VPU and gage requests.

    VPU subsets are the largest (full region); gage subsets vary widely by
    basin size. Random uniform sampling over the ~200 gauge pool gives the
    natural cost distribution (headwater gauges are cheap, basin-outlet
    gauges are expensive).
    """
    # ~40% VPU (consistent heavy), ~60% gage (variable cost)
    if random.random() < 0.4:
        ident = random.choice(VPU_IDS)
        id_type = "vpu_id"
    else:
        ident = random.choice(gages)
        id_type = "gage_id"
    url = f"/api/v1/hydrofabric/{ident}/gpkg?id_type={id_type}&source=nhf&domain=CONUS"
    return "hydrofabric_gpkg", url


def build_parameter_metadata_request(gages: list[str]) -> tuple[str, str]:
    """Parameter metadata with gage_id — always the heavy subset path."""
    mod = random.choice(MODULES)
    gage = random.choice(gages)
    url = f"/api/v1/modules/parameter_metadata/?modules={mod}&gage_id={gage}&domain=CONUS&source=hf"
    return "parameter_metadata", url


def build_streamflow_request(gages: list[str]) -> tuple[str, str]:
    gage = random.choice(gages)
    url = f"/api/v1/streamflow_observations/{gage}/info"
    return "streamflow_info", url


def pick_request(gages: list[str], weights: tuple[int, int, int]) -> tuple[str, str]:
    """Pick a weighted random endpoint. weights = (hf, param, streamflow)."""
    total = sum(weights)
    r = random.randint(1, total)
    if r <= weights[0]:
        return build_hydrofabric_request(gages)
    elif r <= weights[0] + weights[1]:
        return build_parameter_metadata_request(gages)
    else:
        return build_streamflow_request(gages)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
async def fetch_available_gages(client: httpx.AsyncClient) -> list[str]:
    try:
        r = await client.get("/api/v1/streamflow_observations/available?limit=200", timeout=60)
        if r.status_code == 200:
            data = r.json()
            # Endpoint may return dict or list; try common shapes
            if isinstance(data, dict):
                for key in ("identifiers", "ids", "available"):
                    if key in data and isinstance(data[key], list):
                        return [str(x) for x in data[key] if x][:200]
            elif isinstance(data, list):
                return [str(x) for x in data if x][:200]
    except Exception as e:
        print(f"[discover] couldn't fetch /available: {e}")
    return FALLBACK_GAGES


async def one_request(
    client: httpx.AsyncClient,
    ep: str,
    url: str,
    results: Results,
    timeout_s: float,
) -> None:
    started = time.perf_counter()
    wall = time.time()
    status = 0
    err = None
    nbytes = 0
    try:
        # Stream so we don't buffer entire gpkg into memory on the client side
        async with client.stream("GET", url, timeout=timeout_s) as r:
            status = r.status_code
            async for chunk in r.aiter_bytes():
                nbytes += len(chunk)
    except httpx.TimeoutException:
        err = "timeout"
    except httpx.HTTPError as e:
        err = f"http_error:{type(e).__name__}"
    except Exception as e:
        err = f"exc:{type(e).__name__}:{e}"
    latency_ms = (time.perf_counter() - started) * 1000
    results.add(
        Sample(
            endpoint=ep,
            url=url,
            status=status,
            latency_ms=latency_ms,
            error=err,
            bytes=nbytes,
            started_at=wall,
        )
    )


async def run(
    base_url: str,
    rpm: int,
    duration_s: int,
    timeout_s: float,
    weights: tuple[int, int, int],
    out_dir: Path,
) -> Results:
    interval = 60.0 / rpm
    results = Results()
    limits = httpx.Limits(max_connections=64, max_keepalive_connections=32)
    async with httpx.AsyncClient(base_url=base_url, limits=limits) as client:
        # Warm up / discover valid gages
        print("[discover] fetching available gauge IDs...")
        gages = await fetch_available_gages(client)
        print(f"[discover] using {len(gages)} gauge IDs (sample: {gages[:5]})")

        start = time.time()
        tasks: list[asyncio.Task] = []
        issued = 0
        next_fire = start
        while time.time() - start < duration_s:
            now = time.time()
            if now >= next_fire:
                ep, url = pick_request(gages, weights)
                tasks.append(asyncio.create_task(one_request(client, ep, url, results, timeout_s)))
                issued += 1
                next_fire += interval
                if issued % 10 == 0:
                    elapsed = now - start
                    ok = sum(1 for s in results.samples if 200 <= s.status < 300)
                    print(
                        f"[{elapsed:5.0f}s] issued={issued} done={len(results.samples)} "
                        f"ok={ok} inflight={issued - len(results.samples)}"
                    )
            else:
                await asyncio.sleep(min(0.05, next_fire - now))

        # Drain
        print(f"[drain] waiting for {issued - len(results.samples)} in-flight requests...")
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # Persist raw samples as CSV
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "samples.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["started_at", "endpoint", "status", "latency_ms", "bytes", "error", "url"])
        for s in results.samples:
            w.writerow(
                [
                    f"{s.started_at:.3f}",
                    s.endpoint,
                    s.status,
                    f"{s.latency_ms:.1f}",
                    s.bytes,
                    s.error or "",
                    s.url,
                ]
            )
    print(f"[io] wrote {csv_path}")
    return results


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--rpm", type=int, default=100, help="Requests per minute")
    p.add_argument("--duration", type=int, default=300, help="Total test duration in seconds")
    p.add_argument(
        "--timeout",
        type=float,
        default=300,
        help="Per-request timeout seconds (matches ICEFABRIC_HF_GPKG_QUEUE_TIMEOUT_S default).",
    )
    p.add_argument(
        "--weights",
        default="1,2,2",
        help=(
            "Endpoint weights hf,param,stream. Hydrofabric gpkg is heavy (~130 MB / ~30s "
            "per CONUS VPU) so we keep its share modest; a run at 100 rpm with 20% hf "
            "weight still exercises ~20 concurrent heavy gpkg builds per minute."
        ),
    )
    p.add_argument("--out-dir", default="scripts/load_test/results")
    args = p.parse_args()
    weights = tuple(int(x) for x in args.weights.split(","))
    assert len(weights) == 3, "weights must be 3 ints"

    print(f"[cfg] base_url={args.base_url} rpm={args.rpm} duration={args.duration}s weights={weights}")
    results = asyncio.run(
        run(
            base_url=args.base_url,
            rpm=args.rpm,
            duration_s=args.duration,
            timeout_s=args.timeout,
            weights=weights,  # type: ignore[arg-type]
            out_dir=Path(args.out_dir),
        )
    )

    summary = results.summary()
    summary_path = Path(args.out_dir) / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(json.dumps(summary, indent=2))
    print(f"\n[io] wrote {summary_path}")


if __name__ == "__main__":
    main()
