#!/usr/bin/env bash
# run_pipeline.sh —— 端到端跑某个模型
#
# 用法：bash scripts/run_pipeline.sh <model_name> [from_step]
#   from_step ∈ {setup, calibrate, solve, simulate, output}（默认从头）
#
# 设计：薄包装。具体每一步由 agent 通过对应 skill 调度，本脚本只做命令行版兜底。

set -euo pipefail

MODEL_NAME="${1:-}"
FROM_STEP="${2:-setup}"

if [[ -z "$MODEL_NAME" ]]; then
  echo "用法：bash scripts/run_pipeline.sh <model_name> [from_step]"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SPEC_FILE="model/01_setup/${MODEL_NAME}/spec.md"
CALIB_FILE="model/02_calibrate/${MODEL_NAME}/calibration.csv"
TS=$(date +"%Y%m%d_%H%M%S")

echo "========================================"
echo " 模型：${MODEL_NAME}"
echo " 从步骤：${FROM_STEP}"
echo " 时间戳：${TS}"
echo "========================================"

# ---- 0. 预检 ----
if [[ ! -f "$SPEC_FILE" ]]; then
  echo "[ERR] 缺少 spec.md：$SPEC_FILE"
  echo "      请先用 setup-* skill 生成，并通过 model-reviewer 评审。"
  exit 2
fi

REVIEW_GLOB="quality_reports/${MODEL_NAME}_model_review_*.md"
if ! ls $REVIEW_GLOB >/dev/null 2>&1; then
  echo "[ERR] 缺少 model-reviewer 评审记录：$REVIEW_GLOB"
  exit 3
fi

# ---- 1. setup ----
if [[ "$FROM_STEP" == "setup" ]]; then
  echo "[1/5] setup 已完成（spec.md + 评审已存在）"
fi

# ---- 2. calibrate ----
if [[ "$FROM_STEP" == "setup" || "$FROM_STEP" == "calibrate" ]]; then
  echo "[2/5] calibrate"
  if [[ ! -f "$CALIB_FILE" ]]; then
    echo "[ERR] 缺少 calibration.csv：$CALIB_FILE"
    echo "      请用 calibrate-from-moments skill 生成。"
    exit 4
  fi
  echo "      参数表：$CALIB_FILE"
fi

# ---- 3. solve（含稳态校验）----
if [[ "$FROM_STEP" == "setup" || "$FROM_STEP" == "calibrate" || "$FROM_STEP" == "solve" ]]; then
  echo "[3/5] solve"
  # 先稳态校验
  python scripts/check_steady_state.py "output/checkpoints/${MODEL_NAME}_ss.json" \
    || { echo "[ERR] 稳态校验失败"; exit 5; }

  # 推断语言（从 spec.md 第一段读 "实现语言"）
  LANG=$(grep -m1 -E "实现语言|language" "$SPEC_FILE" | head -1)
  echo "      语言推断：$LANG"

  if echo "$LANG" | grep -iq "dynare\|matlab"; then
    bash scripts/run_dynare.sh "model/03_solve/${MODEL_NAME}/${MODEL_NAME}.mod"
  elif echo "$LANG" | grep -iq "julia"; then
    bash scripts/run_julia.sh "model/03_solve/${MODEL_NAME}/run.jl"
  elif echo "$LANG" | grep -iq "gams"; then
    echo "[WARN] GAMS 求解请手动跑：gams model/03_solve/${MODEL_NAME}/main.gms"
  else
    echo "[ERR] 无法推断求解语言，请在 spec.md 中显式声明"
    exit 6
  fi
fi

# ---- 4. simulate ----
if [[ "$FROM_STEP" != "output" ]]; then
  echo "[4/5] simulate"
  echo "      （由 simulate-irf 与 counterfactual-run skill 处理；本脚本不直接调用）"
fi

# ---- 5. output ----
echo "[5/5] output"
if [[ -f "reports/${MODEL_NAME}_analysis.qmd" ]]; then
  if command -v quarto >/dev/null 2>&1; then
    quarto render "reports/${MODEL_NAME}_analysis.qmd"
  else
    echo "[WARN] 未安装 quarto，跳过报告渲染"
  fi
fi

echo "========================================"
echo "  完成：${MODEL_NAME} @ ${TS}"
echo "  下一步：调用 verifier 子 agent 复核"
echo "========================================"
