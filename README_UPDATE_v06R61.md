# Fascinator v0.6R.6.1 User Interest Memory

这个补丁修你刚刚指出的问题：

```text
我对意大利黑帮很感兴趣
```

不应该被当成 question，也不应该丢掉长期价值。它应该是用户偏好/兴趣类断言。

## 新增意图

```text
intent_class = assertion
assertion_subtype = user_interest
handler = Assert_User_Interest
```

## 生成目标

输入：

```text
我对意大利黑帮很感兴趣
```

应生成：

```text
Event_xxx --agent_is--> User
Event_xxx --action_is--> Assert_User_Interest
Event_xxx --patient_is--> User
Event_xxx --topic_is--> Topic_意大利黑帮
User --interested_in--> Topic_意大利黑帮
```

节点仍然只用：

```text
kind = declarative / procedural
tau = semantic / episodic / procedural
```

## 预置核心节点更新

新增：

```text
Assert_User_Interest
Parse_User_Stimulus --routes_to--> Assert_User_Interest
```

覆盖后请再点一次：

```text
写入预置核心节点
```

这样核心处理图里会补上兴趣处理节点。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
backend/data/core_seed_graph.json
frontend/index.html
README_UPDATE_v06R61.md
```
