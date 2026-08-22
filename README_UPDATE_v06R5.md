# Fascinator v0.6R.5 Intent-Routed Ingestion

这版按你刚刚说的路线改：

```text
User said: <用户输入>
→ LLM 解析意图
→ intent_class / assertion_subtype
→ 对应处理节点
→ 从该意图中提取有价值事实
→ Working Event
→ Promote to Pending
→ 可视化审核
→ Commit 知识图谱
```

## 关键变化

### 1. LLM 输入格式

后端 prompt 现在显式使用：

```text
User said: 你的名字是Haru
```

LLM 不再直接生成 Event_X 或完整图谱，而是输出：

```text
intent_class
assertion_subtype
confidence
summary
extracted_values
useful_facts
```

### 2. 意图路由

示例：

```text
你的名字是Haru
```

会被路由为：

```text
intent_class = assertion
assertion_subtype = self_name
handler = Assert_Self_Name
```

然后后端生成：

```text
Event_xxx --agent_is--> User
Event_xxx --action_is--> Assert_Self_Name
Event_xxx --patient_is--> Companion_Self
Event_xxx --name_is--> Name_Haru
Companion_Self --name_is--> Name_Haru
```

```text
我是Hellucigen
```

会被路由为：

```text
intent_class = assertion
assertion_subtype = user_identity
handler = Assert_User_Identity
```

然后生成：

```text
Event_xxx --agent_is--> User
Event_xxx --action_is--> Assert_User_Identity
Event_xxx --patient_is--> User
Event_xxx --name_is--> Name_Hellucigen
User --name_is--> Name_Hellucigen
```

### 3. 预置核心节点

前端顶部新增按钮：

```text
写入预置核心节点
```

会写入：

```text
User
Companion_Self
Parse_User_Stimulus
Assert_Fact
Assert_Self_Name
Assert_User_Identity
Assert_Relationship
Assert_Knowledge
Assert_Goal
Handle_Question
Handle_Command
Handle_Feedback
Ignore_Low_Value
```

这些都是：

```text
kind=declarative/tau=semantic
或
kind=procedural/tau=procedural
```

没有 Concept / Entity / EventFrame / Slot / Attribute / Self / memory=self 那套。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
backend/data/core_seed_graph.json
frontend/index.html
README_UPDATE_v06R5.md
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

## 推荐测试

1. 点“写入预置核心节点”
2. 输入：`你的名字是Haru`
3. 解析为 Working
4. 输入：`我是Hellucigen`
5. 解析为 Working
6. 分别提升为 Pending
7. 在 Pending 可视化审核中确认写入

理想长期图谱应出现：

```text
Companion_Self --name_is--> Name_Haru
User --name_is--> Name_Hellucigen
```
