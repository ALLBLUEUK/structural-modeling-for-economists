---
name: lit-review
description: 文献调研：定位与本模型最近的若干文献并总结其差异。当用户说"文献综述"、"lit review"、"找相关文献"、"前沿"时调用。
type: utility
---

# lit-review — 文献调研

## 触发场景

- "找与本模型最近的 5 篇论文"
- "lit review 写一段"
- "看看这个机制有没有人做过"
- "前沿在哪"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str |  |
| `topic` | str | 研究问题或机制描述 |
| `year_range` | str? | 默认 `2015-2026` |
| `max_papers` | int | 默认 10 |

## 步骤清单

1. 用 `WebFetch` 检索 Google Scholar / NBER / RePEc。
2. 对每篇：提取标题、作者、年份、模型类、机制、识别策略、与本研究的距离。
3. 生成 `quality_reports/<model>_lit_review_<ts>.md`。
4. 指出本模型独特点（gap）。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `quality_reports/<model>_lit_review_<ts>.md` | ✅ |  |
| `master_supporting_docs/<model>_bib.bib` | 建议 | BibTeX 累积 |

## 不允许的操作

- 凭印象编造文献（必须 URL / DOI）
- 把无关论文塞进 review 凑数

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |
