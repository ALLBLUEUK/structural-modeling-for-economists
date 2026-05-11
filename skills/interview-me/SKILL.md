---
name: interview-me
description: 反向访谈研究生以厘清机制设定（在 spec 模糊时调用）。当用户说"我也不太确定"、"帮我想清楚"、"interview me"时调用。
type: utility
---

# interview-me — 反向访谈

## 触发场景

- "我也不太确定要研究啥"
- "帮我把机制想清楚"
- "interview me"
- "spec 里某段写不出来"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `topic` | str | 用户当前模糊的领域 |
| `max_rounds` | int | 默认 5 轮一对一问答 |

## 步骤清单

1. agent 提出一组结构化问题（先广后窄）：研究问题、关键机制、变量、目标矩。
2. 用户回答；agent 把答案写入 `model/01_setup/<model>/spec_draft.md` 对应段。
3. 若答案模糊，追问；若清晰，固化。
4. 结束时给出 spec 草稿与剩余 TBD 清单。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `model/01_setup/<model>/spec_draft.md` | ✅ |  |
| `logs/<model>_interview_<ts>.md` | ✅ |  |

## 不允许的操作

- 给用户的答案打分或评判（任务是抽取，不是审判）
- 跳过追问直接落入 spec

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |
