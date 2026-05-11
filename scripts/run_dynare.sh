#!/usr/bin/env bash
# run_dynare.sh —— 在 MATLAB 或 Octave 中跑一个 .mod 文件
# 用法：bash scripts/run_dynare.sh model/03_solve/<model>/<model>.mod

set -euo pipefail

MOD_FILE="${1:-}"
if [[ -z "$MOD_FILE" || ! -f "$MOD_FILE" ]]; then
  echo "用法：bash scripts/run_dynare.sh <path_to.mod>"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODEL_DIR=$(dirname "$MOD_FILE")
MODEL_BASE=$(basename "$MOD_FILE" .mod)
TS=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/${MODEL_BASE}_dynare_${TS}.log"

mkdir -p logs

# 优先 MATLAB，其次 Octave
if command -v matlab >/dev/null 2>&1; then
  echo "[run_dynare] 使用 MATLAB"
  matlab -nodisplay -nosplash -r "try; cd('${MODEL_DIR}'); dynare ${MODEL_BASE} noclearall; catch ME; disp(ME.message); exit(1); end; exit;" \
    2>&1 | tee "$LOG_FILE"
elif command -v octave >/dev/null 2>&1; then
  echo "[run_dynare] 使用 Octave"
  octave --no-gui --eval "cd('${MODEL_DIR}'); dynare ${MODEL_BASE} noclearall;" 2>&1 | tee "$LOG_FILE"
else
  echo "[ERR] 既找不到 matlab 也找不到 octave"
  exit 2
fi

echo "[run_dynare] 日志：$LOG_FILE"
