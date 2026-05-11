#!/usr/bin/env python3
"""log-reminder.py —— 会话结束时提醒：是否记录了 session log。"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

LOG_DIR = Path("logs/sessions")

def main() -> int:
    if not LOG_DIR.exists():
        print("[log-reminder] 提示：本会话未创建 logs/sessions/。"
              "如本次有重要建模操作，请用 templates/session-log.md 记录。")
        return 0

    cutoff = datetime.now() - timedelta(hours=2)
    recent = [p for p in LOG_DIR.glob("*.md")
              if datetime.fromtimestamp(p.stat().st_mtime) > cutoff]

    if not recent:
        print("[log-reminder] 最近 2 小时未更新 session log。"
              "如本次会话有产物变更，建议补一份记录。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
