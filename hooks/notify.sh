#!/usr/bin/env bash
# notify.sh —— 长任务完成时桌面通知（可选钩子）
#
# 由 .claude/settings.json 在指定生命周期事件触发；当前默认未启用。
# 用户可手动从 settings.json 启用，或从 scripts/run_pipeline.sh 末尾 sourced。
#
# 跨平台尝试顺序：
#   1. Windows  -> powershell BurntToast / msg
#   2. macOS    -> osascript display notification
#   3. Linux    -> notify-send

set -eu

TITLE="${1:-strucmod}"
MSG="${2:-task finished}"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    powershell -NoProfile -Command \
      "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; \
       [System.Windows.Forms.MessageBox]::Show('$MSG','$TITLE')" 2>/dev/null \
    || echo "[notify] $TITLE: $MSG"
    ;;
  Darwin)
    osascript -e "display notification \"$MSG\" with title \"$TITLE\"" 2>/dev/null \
      || echo "[notify] $TITLE: $MSG"
    ;;
  Linux)
    notify-send "$TITLE" "$MSG" 2>/dev/null \
      || echo "[notify] $TITLE: $MSG"
    ;;
  *)
    echo "[notify] $TITLE: $MSG"
    ;;
esac

exit 0
