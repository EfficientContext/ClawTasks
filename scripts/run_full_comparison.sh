#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────
# Full benchmark comparison: ContextPilot vs Baseline
#
# Prerequisites:
#   - Docker image "contextpilot-sglang" built
#   - OPENAI_API_KEY set (for judge eval with gpt-5.4-mini)
#   - GPU available
#
# Usage:
#   bash scripts/run_full_comparison.sh
#   bash scripts/run_full_comparison.sh --topic paper-transformer   # single topic
#   bash scripts/run_full_comparison.sh --model Qwen/Qwen2.5-7B-Instruct  # custom model
# ─────────────────────────────────────────────────────────

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
TOPIC_FILTER=""
TASKS_FILE="openclaw_tasks_all.json"
SGLANG_PORT=30000
CP_PORT=8765
TIMEOUT=180
JUDGE_MODEL="gpt-5.4-mini"
CONTAINER_NAME_CP="clawbench-contextpilot"
CONTAINER_NAME_BL="clawbench-baseline"

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --topic) TOPIC_FILTER="--topic $2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --judge-model) JUDGE_MODEL="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BENCH_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BENCH_DIR"

echo "============================================================"
echo "Full Benchmark Comparison"
echo "  Model:       $MODEL"
echo "  Tasks:       $TASKS_FILE"
echo "  Topic:       ${TOPIC_FILTER:-all}"
echo "  Timeout:     ${TIMEOUT}s"
echo "  Judge:       $JUDGE_MODEL"
echo "============================================================"

cleanup() {
    echo ""
    echo "Cleaning up containers..."
    docker rm -f "$CONTAINER_NAME_CP" 2>/dev/null || true
    docker rm -f "$CONTAINER_NAME_BL" 2>/dev/null || true
}
trap cleanup EXIT

wait_for_health() {
    local url="$1"
    local name="$2"
    local max_wait=300
    local elapsed=0
    echo -n "  Waiting for $name..."
    while ! curl -s "$url" >/dev/null 2>&1; do
        sleep 2
        elapsed=$((elapsed + 2))
        if [ $elapsed -ge $max_wait ]; then
            echo " TIMEOUT after ${max_wait}s"
            exit 1
        fi
        echo -n "."
    done
    echo " ready (${elapsed}s)"
}

wait_for_sglang() {
    local port="$1"
    local name="$2"
    local max_wait=300
    local elapsed=0
    echo -n "  Waiting for $name model load..."
    while true; do
        status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}/health" 2>/dev/null || echo "000")
        if [ "$status" = "200" ]; then
            break
        fi
        sleep 3
        elapsed=$((elapsed + 3))
        if [ $elapsed -ge $max_wait ]; then
            echo " TIMEOUT after ${max_wait}s"
            exit 1
        fi
        echo -n "."
    done
    echo " ready (${elapsed}s)"
}

# ─────────────────────────────────────────────────────────
# Run 1: ContextPilot (SGLang + ContextPilot proxy)
# ─────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "[1/2] Starting ContextPilot run"
echo "============================================================"

docker rm -f "$CONTAINER_NAME_CP" 2>/dev/null || true

echo "  Starting container: $CONTAINER_NAME_CP"
docker run -d --gpus all \
    --name "$CONTAINER_NAME_CP" \
    -p ${CP_PORT}:8765 \
    -p ${SGLANG_PORT}:30000 \
    contextpilot-sglang \
    --model-path "$MODEL"

wait_for_sglang "$SGLANG_PORT" "SGLang"
wait_for_health "http://localhost:${CP_PORT}/" "ContextPilot"

echo "  Running benchmark with ContextPilot..."
python scripts/run_bench.py \
    --tasks-file "$TASKS_FILE" \
    --runner openai \
    --model "$MODEL" \
    --timeout "$TIMEOUT" \
    $TOPIC_FILTER \
    --evaluate \
    --judge-model "$JUDGE_MODEL" \
    2>&1 | tee /tmp/clawbench_cp_run.log

# Extract the results file path from output
CP_RESULTS=$(grep "^Output:" /tmp/clawbench_cp_run.log | tail -1 | awk '{print $2}')
if [ -z "$CP_RESULTS" ]; then
    echo "ERROR: Could not find ContextPilot results file"
    exit 1
fi
echo "  ContextPilot results: $CP_RESULTS"

echo "  Stopping ContextPilot container..."
docker rm -f "$CONTAINER_NAME_CP" 2>/dev/null || true
sleep 3

# ─────────────────────────────────────────────────────────
# Run 2: Baseline (plain SGLang, no ContextPilot)
# ─────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "[2/2] Starting Baseline run"
echo "============================================================"

docker rm -f "$CONTAINER_NAME_BL" 2>/dev/null || true

echo "  Starting container: $CONTAINER_NAME_BL (plain SGLang)"
docker run -d --gpus all \
    --name "$CONTAINER_NAME_BL" \
    -p ${SGLANG_PORT}:30000 \
    lmsysorg/sglang:latest \
    python3 -m sglang.launch_server \
    --model-path "$MODEL" \
    --host 0.0.0.0 \
    --port 30000

wait_for_sglang "$SGLANG_PORT" "SGLang (baseline)"

echo "  Running benchmark without ContextPilot..."
OPENAI_BASE_URL="http://localhost:${SGLANG_PORT}/v1" \
python scripts/run_bench.py \
    --tasks-file "$TASKS_FILE" \
    --runner openai \
    --model "$MODEL" \
    --timeout "$TIMEOUT" \
    $TOPIC_FILTER \
    --evaluate \
    --judge-model "$JUDGE_MODEL" \
    2>&1 | tee /tmp/clawbench_bl_run.log

BL_RESULTS=$(grep "^Output:" /tmp/clawbench_bl_run.log | tail -1 | awk '{print $2}')
if [ -z "$BL_RESULTS" ]; then
    echo "ERROR: Could not find Baseline results file"
    exit 1
fi
echo "  Baseline results: $BL_RESULTS"

echo "  Stopping baseline container..."
docker rm -f "$CONTAINER_NAME_BL" 2>/dev/null || true

# ─────────────────────────────────────────────────────────
# Compare
# ─────────────────────────────────────────────────────────
echo ""
echo ""
python scripts/compare_runs.py \
    "$CP_RESULTS" \
    "$BL_RESULTS" \
    --label-a "ContextPilot" \
    --label-b "Baseline"
