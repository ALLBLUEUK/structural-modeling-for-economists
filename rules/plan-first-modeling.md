# Plan-First Modeling — 计划先行协议

## 核心原则

**任何模型代码动手之前，必须先有 `spec.md` 并通过 `model-reviewer` 评审。**

这一原则不可绕过，理由：

- 结构建模的错误成本极高：方程错一行，后面全错。
- 数学错误 90% 来自机制叙述与方程不对应，spec.md 强制先写自然语言机制再写方程。
- 校准、求解、仿真、写作都引用 spec.md 作为单一事实源。
- AI agent 容易在没有 spec 的情况下自作主张拼凑方程；spec 强制人类与 agent 对齐。

## spec.md 的最小必备字段

按 `templates/model-spec-template.md` 的顺序：

1. 经济问题与机制
2. 时间环境（离散/连续、有限/无限期）
3. 代理人列表
4. 变量分类表（**所有**内生 + 外生 + 价格变量）
5. 方程系统（按代理人 + 出清 + 外生过程分组）
6. 函数形式
7. 参数表（含校准来源占位）
8. 求解方法
9. 验证目标（稳态矩、复现目标、IRF 形状先验）

## 评审通过标准

`model-reviewer` 必须给出 "通过" 或 "修改后通过"，并写入 `quality_reports/<model>_model_review_<timestamp>.md`。

"修改后通过" 视为有条件通过：必须先把建议清单全部 tick，再进入下一阶段。

## 例外

无。

唯一允许跳过 spec 的场景是 `explorations/` 目录中的一次性原型实验。但这类实验的产物**不得**进入 `model/` 主流水线，也不得写入 `output/`。

## 与外部 plan-first 实践的对齐

Anthropic 的 superpowers 插件（如其中的 brainstorming 与 writing-plans 技能）在更广泛的软件工程语境下提倡相同原则——"动手前先写设计文档并获得评审"。本协议是这一原则在结构建模领域的特化，**不依赖**任何外部插件即可执行；如果用户已安装 superpowers，可作为补充。
