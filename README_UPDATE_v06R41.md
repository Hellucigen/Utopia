# Fascinator v0.6R.4.1 Event Head Canonical Fix

这个补丁修复 v0.6R.4 中 LLM 把 prompt 示例里的 `Event_X` 复制进候选图的问题。

## 修复点

1. 不再保留 LLM 的 `Event_X`。LLM 输出中的 `Event_X` 或任意 `Event_*` 都会被 remap 到本次真正生成的 `Event_<timestamp>`。

2. 修复 event_kind / summary 被 schema 词污染的问题。  
比如 `event_kind=declarative`、`summary=episodic` 会被改回合理值。

3. 同一条 `src --relation--> dst` 会去重。

4. 节点模型保持你的论文式结构：

```text
kind = declarative / procedural
tau = semantic / episodic / procedural
```

事件框架仍然通过边表达属性：

```text
Event_xxx --agent_is--> User
Event_xxx --action_is--> Assign_Name
Event_xxx --patient_is--> Companion_Self
Event_xxx --name_is--> Name_Haru
Companion_Self --name_is--> Name_Haru
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R41.md
```
