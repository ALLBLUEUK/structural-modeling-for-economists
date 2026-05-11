---
name: commit
description: git 提交：检查 .gitignore、生成提交信息、避免提交受保护文件。当用户说"提交"、"commit"、"push"、"git"时调用。
type: utility
---

# commit — git 提交工具

## 触发场景

- "提交一下当前进度"
- "做个 commit"
- "把这一节的修改 push 上去"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `scope` | str | 本次提交的主题 |
| `files` | list[path]? | 可选：白名单 |

## 步骤清单

1. 跑 `python scripts/check_data_safety.py --staged $(git diff --cached --name-only)`。
2. 若有暂存的 `data/raw/` 或 `data/derived/` → 拒绝并报警。
3. 运行 `git status` 与 `git diff` 摘要。
4. 依据 `scope` 与最近三个 commit 的风格，起草 commit message。
5. 由用户确认后 `git commit`。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| git commit | ✅ | 新 commit |
| `logs/commit_<ts>.log` | 建议 |  |

## 不允许的操作

- 强制 push（除非用户明确指令）
- 提交 `data/raw/` 或包含密钥的文件
- 用 `--no-verify` 跳过 hooks

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |
