#!/usr/bin/env bash
# run_matlab.sh —— 在 MATLAB 中跑非 Dynare 类的 .m 脚本
# 用法：bash scripts/run_matlab.sh model/03_solve/<model>/main.m
#
# 仅适用于"非 Dynare"调用。Dynare 用 scripts/run_dynare.sh。

set -euo pipefail

M_FILE="${1:-}"
if [[ -z "$M_FILE" || ! -f "$M_FILE" ]]; then
  echo "用法：bash scripts/run_matlab.sh <path_to.m>"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v matlab >/dev/null 2>&1; then
  echo "[ERR] 未找到 matlab"
  exit 2
fi

MODEL_DIR=$(dirname "$M_FILE")
MODEL_BASE=$(basename "$M_FILE" .m)
TS=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/${MODEL_BASE}_matlab_${TS}.log"
mkdir -p logs

echo "[run_matlab] 调用：$M_FILE"
echo "[run_matlab] 日志：$LOG_FILE"

matlab -nodisplay -nosplash -nodesktop -r \
  "try; cd('$MODEL_DIR'); run('${MODEL_BASE}.m'); catch ME; disp(getReport(ME)); exit(1); end; exit;" \
  2>&1 | tee "$LOG_FILE"
