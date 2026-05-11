#!/usr/bin/env bash
# protect-files.sh —— 阻止意外修改受保护文件
# 由 .claude/settings.json 在 Edit / Write 之后触发

PROTECTED=(
  "model/00_master.mod"
  "model/00_master.jl"
  "model/00_master.m"
  "model/00_master.gms"
  ".gitignore"
  ".gitattributes"
  "model/_utils/seed.txt"
)

# 简单实现：本 hook 不知道刚刚改了什么，只在改动后做一次警告
# 真实生产中应解析事件 payload。
echo "[protect-files] 受保护文件清单：${PROTECTED[*]}"
echo "[protect-files] 如确需修改，请在 commit 信息中显式说明理由。"
exit 0
