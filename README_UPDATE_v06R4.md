# Fascinator v0.6R.4 Memory-Kind Node Model Rewrite

这版按你刚刚纠正的定义重写：

```text
节点 v = (id, kind, tau, weight, activation, attributes)
```

## 节点 kind

只允许：

```text
declarative  陈述性记忆
procedural   程序性记忆
```

## 陈述性记忆再分 tau

```text
semantic     语义记忆
episodic     情景记忆
```

程序性记忆：

```text
kind=procedural
tau=procedural
```

## 不再使用这些乱七八糟的节点类型

生成候选时不再使用：

```text
Concept
Entity
EventFrame
Slot
Action
Rule
Emotion
Personality
Intent
Expectation
Parameter
Attribute
Self
memory=self
```

这些如果存在于旧图谱里，后端会在读取时迁移成新模型。

## 事件框架表达方式

事件框架不是 Slot 节点集合。

事件框架是一个：

```json
{
  "id": "Event_xxx",
  "kind": "declarative",
  "tau": "episodic"
}
```

然后通过边表达属性：

```text
Event_xxx --agent_is--> User
Event_xxx --action_is--> Assign_Name
Event_xxx --patient_is--> Companion_Self
Event_xxx --name_is--> Name_Haru
```

类似：

```text
Head_Node --color_is--> Blue
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R4.md
```

## 使用

解压到：

```text
E:\Utopia
```

覆盖同名文件，重启：

```powershell
cd E:\Utopia
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

前端 Ctrl + F5。

## 测试

输入：

```text
你的名字是Haru
```

理想候选：

```text
Event_xxx: kind=declarative, tau=episodic
User: kind=declarative, tau=semantic
Companion_Self: kind=declarative, tau=semantic
Assign_Name: kind=procedural, tau=procedural
Name_Haru: kind=declarative, tau=semantic

Event_xxx --agent_is--> User
Event_xxx --action_is--> Assign_Name
Event_xxx --patient_is--> Companion_Self
Event_xxx --name_is--> Name_Haru
Companion_Self --name_is--> Name_Haru
```
