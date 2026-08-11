#!/usr/bin/env bash
# Orchestrate: build → start container → wait healthy → monitor + load test → teardown.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

RESULTS="results"
mkdir -p "$RESULTS"

# DURATION, RPM (requests per minute), TIMEOUT, CPUS, and MEMORY can be set as environment variables,
# otherwise the defaults are used.
DURATION="${DURATION:-300}"   # seconds
RPM="${RPM:-100}"
TIMEOUT="${TIMEOUT:-120}"     # per-request seconds
CPUS="${CPUS:-2.0}"
MEMORY="${MEMORY:-8g}"

echo "== config: rpm=$RPM duration=${DURATION}s per-req-timeout=${TIMEOUT}s cpus=$CPUS mem=$MEMORY =="

# Use docker compose v2 if available, else fall back to docker-compose v1.
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
else
    DC="docker-compose"
fi
echo "== using compose: $DC =="

# --- Build ---
echo "== building api image =="
$DC -f docker-compose.load.yml build api

# --- Start ---
echo "== starting container =="
$DC -f docker-compose.load.yml up -d api

# Apply runtime caps (compose v2 ignores top-level cpus/mem_limit without swarm;
# make it explicit with docker update after start).
docker update --cpus="$CPUS" --memory="$MEMORY" --memory-swap="$MEMORY" \
    icefabric-api-loadtest >/dev/null
echo "== applied --cpus=$CPUS --memory=$MEMORY =="

# --- Wait for healthy ---
echo "== waiting for /health (up to 10 min, cache build takes time) =="
for i in $(seq 1 120); do
    if curl -fsS --max-time 3 http://localhost:8000/health >/dev/null 2>&1; then
        echo "== api is healthy after $((i*5))s =="
        break
    fi
    sleep 5
    if [[ $((i % 12)) -eq 0 ]]; then
        echo "   still waiting... ($((i*5))s elapsed)"
    fi
done
if ! curl -fsS --max-time 3 http://localhost:8000/health >/dev/null 2>&1; then
    echo "!! api never became healthy. Last 80 lines of container logs:"
    docker logs --tail 80 icefabric-api-loadtest || true
    exit 1
fi

# --- Monitor ---
echo "== starting docker-stats monitor =="
bash monitor.sh icefabric-api-loadtest "$RESULTS/stats.csv" 2 &
MON_PID=$!
trap 'kill $MON_PID 2>/dev/null || true; $DC -f docker-compose.load.yml logs api > "$RESULTS/container.log" 2>&1 || true' EXIT

# --- Load test ---
echo "== running load test =="
python3 load_test.py \
    --base-url http://localhost:8000 \
    --rpm "$RPM" \
    --duration "$DURATION" \
    --timeout "$TIMEOUT" \
    --out-dir "$RESULTS"

# --- Stop monitor, dump logs, analyze ---
kill $MON_PID 2>/dev/null || true
sleep 2
$DC -f docker-compose.load.yml logs api > "$RESULTS/container.log" 2>&1 || true

echo ""
echo "== resource analysis =="
python3 analyze.py --stats "$RESULTS/stats.csv"

echo ""
echo "== container state =="
docker inspect icefabric-api-loadtest \
    --format '{{.State.Status}} OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}} RestartCount={{.RestartCount}}'

echo ""
echo "== grep for errors / OOM / tracebacks in container log =="
grep -i -E "oom|killed|memoryerror|traceback|error" "$RESULTS/container.log" | head -30 || true

echo ""
echo "results in: $HERE/$RESULTS"
