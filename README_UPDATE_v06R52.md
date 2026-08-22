# Fascinator v0.6R.5.2 LLM Useful Facts Filter

这个补丁修复你刚刚看到的问题：

```text
Haru --is_named_by--> 用户
```

这种是 LLM 在 `useful_facts` 里额外生成的噪声事实。  
对于明确可判定的意图，后端 handler 应该是权威来源，不能让 LLM 额外塞奇怪事实。

## 修复策略

对于这些 deterministic subtype：

```text
self_name
user_identity
relationship
goal
knowledge_is_a
knowledge_has
```

后端只保留 handler 生成的候选事实，忽略 LLM 的 `useful_facts`。

例如：

```text
你的名字是Haru
```

应该只生成：

```text
Event_xxx --agent_is--> User
Event_xxx --action_is--> Assert_Self_Name
Event_xxx --patient_is--> Companion_Self
Event_xxx --name_is--> Name_Haru
Companion_Self --name_is--> Name_Haru
```

不会再出现：

```text
Haru --is_named_by--> 用户
```

对于开放式事实教学，例如复杂知识句，仍然允许 LLM useful_facts 参与。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R52.md
```
