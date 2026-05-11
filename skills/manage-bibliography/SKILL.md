---
name: manage-bibliography
description: 管 paper/references.bib：增删 BibTeX entry、查重、按引用风格规范化（AEA / Chicago author-date）、清未引用条目。当用户说"加引用"、"查文献"、"manage bib"时调用。
type: paper-composition
---

# manage-bibliography — 文献管理

## 触发场景

- 写作过程中临时需要新引用
- 论文完成后审计引用 / 清理未用 entry
- 修正 BibTeX 格式

## 输入契约

| 字段 | 说明 |
|---|---|
| `bib_path` | 默认 `paper/references.bib` |
| `op` | enum: `add` / `lookup` / `dedupe` / `audit` / `format` |
| `payload` | 依 op 而定（add → 引用源；lookup → 关键字；audit → 无） |

## 步骤清单

### add — 加引用

1. 输入：DOI / 标题 / 作者+年份 / 完整 BibTeX 文本之一
2. 若 DOI：调 `WebFetch` 从 doi.org 取 BibTeX
3. 若仅标题：建议用户用 Google Scholar / NBER / RePEc 搜索后给 DOI
4. 规范化 entry：
   - 用 author-year-firstword 形式的 key（如 `KingRebelo1999`、`Aiyagari1994`）
   - 字段顺序：`author, title, journal, year, volume, number, pages, doi`
   - 字符串字段加 `{}` 包保护大小写（如 `{R}eal {B}usiness {C}ycle`）
5. 追加到 `references.bib`，按 key 字母序插入

### lookup — 在 .bib 中查关键字

`Grep` 找 author 或 title 关键词，返回所有匹配 entry 的 key 与摘要。

### dedupe — 去重

按 DOI 优先、其次按 title+year，找出重复条目；提示用户保留哪一份。

### audit — 引用审计

1. 用 `Grep` 在 `paper/sections/*.tex` 与 `paper/appendix/*.tex` 中找所有 `\cite[tp]?{}` 调用，提取 key
2. 与 `references.bib` 中已有 key 比对：
   - 引用了但 .bib 缺 → 报错，提示用户补 entry
   - .bib 有但未被引用 → 警告（可选清理）
3. 输出 `quality_reports/<project>_bib_audit_<ts>.md`

### format — 规范化

按 AEA / Chicago author-date 规范统一字段顺序、删除冗余 fields、统一缩写（"\textit{Econometrica}" vs "Econometrica"）。

## 输出契约

| op | 必产 |
|---|---|
| add | `paper/references.bib` 更新 |
| lookup | 控制台输出匹配 key 与摘要 |
| dedupe | 报告 + 用户确认后清理 |
| audit | `quality_reports/<project>_bib_audit_<ts>.md` |
| format | `paper/references.bib` 规范化 |

## 不允许

- 编造 entry（必须有 DOI 或可验证来源）
- 删除被引用的 entry
- 改动用户已 polish 的 entry 排版（仅在 op=format 显式触发时改）

## 失败回退

| 症状 | 处理 |
|---|---|
| DOI 解析失败 | 提示用户手粘 BibTeX，不强猜 |
| audit 发现缺引用 | 阻断 `render-paper`，必须先补 |
