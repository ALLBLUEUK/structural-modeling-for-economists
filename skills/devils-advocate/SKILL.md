---
name: devils-advocate
description: 反方拷问：质疑模型机制、识别策略、数值结果。当用户说"挑刺"、"反驳一下"、"devils advocate"、"audit"时调用。
type: reviewer
---

# devils-advocate — 反方拷问

## 触发场景

- "挑刺挑刺"
- "反方角度看一下"
- "找漏洞"
- "审稿人会怎么打回去"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str |  |
| `focus` | enum | `mechanism` / `identification` / `numerics` / `welfare` / `all` |

## 步骤清单

1. 扮演审稿人：把 `spec.md`、`equations.tex`、IRF 报告、quality_reports 全读一遍。
2. 对每个声称（机制、参数、识别、IRF 形态）提一个尖锐问题。
3. 形成不少于 10 条的 reject reasons 清单。
4. 为每条给一个最少修改路径或反驳。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `quality_reports/<model>_devils_advocate_<ts>.md` | ✅ |  |

## 不允许的操作

- 礼貌让步（任务是拷问，不是和事佬）
- 重复 model-reviewer 已经报过的问题（互补，不重复）

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |
