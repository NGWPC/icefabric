#!/usr/bin/env bash
# Stream `docker stats` into a CSV for later analysis.
# Usage: ./monitor.sh <container> <out_csv> [interval_seconds]
set -euo pipefail

CONTAINER="${1:-icefabric-api-loadtest}"
OUT="${2:-scripts/load_test/results/stats.csv}"
INTERVAL="${3:-2}"

mkdir -p "$(dirname "$OUT")"
echo "timestamp,name,cpu_pct,mem_usage,mem_limit,mem_pct,net_io,block_io,pids" > "$OUT"

while true; do
  ts=$(date +%s)
  # --no-stream gives one snapshot; we parse its non-header line
  docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}' \
    "$CONTAINER" 2>/dev/null | while IFS=, read -r name cpu mem mempct net block pids; do
      # Split "123.4MiB / 8GiB" into usage,limit
      usage=$(echo "$mem" | awk -F' / ' '{print $1}')
      limit=$(echo "$mem" | awk -F' / ' '{print $2}')
      printf '%s,%s,%s,%s,%s,%s,"%s","%s",%s\n' \
        "$ts" "$name" "$cpu" "$usage" "$limit" "$mempct" "$net" "$block" "$pids" >> "$OUT"
    done || true
  sleep "$INTERVAL"
done
