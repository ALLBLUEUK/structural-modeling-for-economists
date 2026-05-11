#!/usr/bin/env bash
# run_julia.sh —— 在 Julia 中跑一个脚本
# 用法：bash scripts/run_julia.sh model/03_solve/<model>/run.jl

set -euo pipefail

JL_FILE="${1:-}"
if [[ -z "$JL_FILE" || ! -f "$JL_FILE" ]]; then
  echo "用法：bash scripts/run_julia.sh <path_to.jl>"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v julia >/dev/null 2>&1; then
  echo "[ERR] 未找到 julia"
  exit 2
fi

MODEL_BASE=$(basename "$(dirname "$JL_FILE")")
TS=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/${MODEL_BASE}_julia_${TS}.log"
mkdir -p logs

julia --project=. --color=no "$JL_FILE" 2>&1 | tee "$LOG_FILE"
echo "[run_julia] 日志：$LOG_FILE"
