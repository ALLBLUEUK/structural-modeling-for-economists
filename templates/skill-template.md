---
name: <skill-name>
description: <一句话描述触发场景与用途。要写得让 agent 能够仅从 description 判断"是否调用我"。>
type: <setup | calibrate | solver | simulator | validator | orchestrator | reviewer | utility>
---

# <skill-name> — <中文短描>

## 触发场景

- "<场景 1>"
- "<场景 2>"
- "<场景 3>"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | |
| ... | | |

## 前置条件

- [ ] 必须存在 ...
- [ ] 必须通过 ...

## 步骤清单

### Step 1. <动作>

…

### Step 2. <动作>

…

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| ... | ✅ | |

## 不允许

- ...

## 失败回退

| 症状 | 处理 |
|---|---|
| ... | ... |
