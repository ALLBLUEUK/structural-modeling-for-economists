---
name: proofread
description: 对论文段落、方程注释、报告做语言层面的校对。当用户说"校对"、"proofread"、"语言润色"、"polish"时调用。
type: utility
---

# proofread — 语言校对

## 触发场景

- "校对这一段"
- "proofread 报告"
- "语言润色"
- "polish"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `file_path` | path | 要校对的 .md / .tex / .qmd |
| `style` | enum | `academic_en` / `academic_zh` / `casual` |

## 步骤清单

1. 读文件。
2. 改：拼写、语法、术语一致性、句子长度、被动 vs 主动语态。
3. 保留：所有数字、引用、变量名、方程编号。
4. 输出 diff（不是直接覆盖），交用户确认后 apply。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| diff 草案 | ✅ | 只读交付，不直接 write |

## 不允许的操作

- 改动数字 / 引用 / 变量名 / 公式
- 改语义（只改语言）

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |
