"""Summarise stats.csv from monitor.sh — look for memory creep, OOM proximity, CPU saturation."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def to_bytes(s: str) -> float:
    s = s.strip()
    m = re.match(r"([0-9.]+)\s*([KMGT]?i?B)", s, re.I)
    if not m:
        return 0.0
    v = float(m.group(1))
    unit = m.group(2).lower()
    mult = {
        "b": 1,
        "kb": 1e3,
        "mb": 1e6,
        "gb": 1e9,
        "tb": 1e12,
        "kib": 1024,
        "mib": 1024**2,
        "gib": 1024**3,
        "tib": 1024**4,
    }.get(unit, 1)
    return v * mult


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--stats", default="scripts/load_test/results/stats.csv")
    args = p.parse_args()
    path = Path(args.stats)
    if not path.exists():
        print(f"no stats file at {path}")
        return

    rows = list(csv.DictReader(path.open()))
    if not rows:
        print("no samples")
        return

    cpu_vals = [float(r["cpu_pct"].rstrip("%")) for r in rows if r["cpu_pct"]]
    mem_vals = [to_bytes(r["mem_usage"]) for r in rows if r["mem_usage"]]
    mem_pct_vals = [float(r["mem_pct"].rstrip("%")) for r in rows if r["mem_pct"]]

    def q(xs, p):
        if not xs:
            return 0.0
        xs = sorted(xs)
        return xs[int((p / 100.0) * (len(xs) - 1))]

    print(f"samples: {len(rows)}")
    print(
        f"cpu %   min={min(cpu_vals):6.1f} mean={sum(cpu_vals) / len(cpu_vals):6.1f} "
        f"p95={q(cpu_vals, 95):6.1f} max={max(cpu_vals):6.1f}"
    )
    print(
        f"mem GiB min={min(mem_vals) / 1024**3:6.2f} mean={sum(mem_vals) / len(mem_vals) / 1024**3:6.2f} "
        f"p95={q(mem_vals, 95) / 1024**3:6.2f} max={max(mem_vals) / 1024**3:6.2f}"
    )
    print(
        f"mem %   min={min(mem_pct_vals):6.1f} mean={sum(mem_pct_vals) / len(mem_pct_vals):6.1f} "
        f"p95={q(mem_pct_vals, 95):6.1f} max={max(mem_pct_vals):6.1f}"
    )

    # Creep detection: compare first-third vs last-third mean memory
    third = len(mem_vals) // 3
    if third >= 3:
        head = sum(mem_vals[:third]) / third
        tail = sum(mem_vals[-third:]) / third
        creep = (tail - head) / max(head, 1)
        print(f"mem creep (last-third vs first-third): {creep * 100:+.1f}%")
        if creep > 0.25:
            print("  ⚠️  > 25% growth — possible leak or unbounded caching")
        elif creep > 0.10:
            print("  ⚠️  > 10% growth — keep an eye on it over a longer run")
        else:
            print("  ✅ memory stable")


if __name__ == "__main__":
    main()
