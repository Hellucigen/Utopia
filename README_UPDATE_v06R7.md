# Fascinator v0.6R.7 General Assertion Frame

这版解决“每来一种句子都要加更新包”的问题。

## 新主线

```text
User said: <用户输入>
→ LLM 判断少量高层意图
→ LLM 抽取通用候选事实边
→ 后端规范化节点/关系/证据
→ Working Event
→ Promote to Pending
→ 可视化审核
→ Commit
```

## 不再依赖大量 subtype handler

高层 intent 只保留：

```text
assertion
question
command
feedback
low_value
```

assertion 内部不再靠不断增加：

```text
user_interest
user_habit
user_plan
user_opinion
...
```

而是统一抽取：

```text
src --relation--> dst
```

例如：

```text
我对意大利黑帮很感兴趣
User --interested_in--> Topic_意大利黑帮

我最近在学强化学习
User --currently_learning--> Topic_强化学习

我不喜欢太复杂的UI
User --dislikes--> Topic_太复杂的UI

Haru应该优先保持图谱整洁
Companion_Self --should_prioritize--> Goal_图谱整洁

机器人需要传感器感知环境
Robot --requires--> Sensor
Sensor --supports--> Environment_Perception
```

## 事件框架

每句话仍然生成一个情景事件头：

```text
Event_xxx: kind=declarative, tau=episodic
```

并通过边表达：

```text
Event_xxx --agent_is--> User
Event_xxx --action_is--> Assert_Statement
Event_xxx --topic_is/name_is/object_is--> ...
```

候选事实边带证据：

```json
{
  "derived_from_event": "Event_xxx",
  "requires_review": true
}
```

## 预置核心节点新增

```text
Assert_Statement
Extract_Useful_Facts
Parse_User_Stimulus --routes_to--> Assert_Statement
Assert_Statement --uses--> Extract_Useful_Facts
```

覆盖后请再点一次：

```text
写入预置核心节点
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
backend/data/core_seed_graph.json
frontend/index.html
README_UPDATE_v06R7.md
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

```text
我对意大利黑帮很感兴趣
我最近在学强化学习
我不喜欢太复杂的UI
Haru应该优先保持图谱整洁
机器人需要传感器感知环境
```

重点看是否都能生成合理的：

```text
src --relation--> dst
```
