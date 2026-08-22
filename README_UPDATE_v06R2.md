# Fascinator v0.6R.2 LLM EventFrame Parser

这个版本把 Stimulus 主线改成：

```text
Stimulus
→ LLM 解析为 Working EventFrame
→ 从 EventFrame 中抽取有价值图谱事实
→ Working 预览
→ Promote to Pending
→ Pending 审核
→ Commit 到长期知识图谱
```

仍然不做回复功能；回复、对话代理、工具执行策略后面再说。

## 覆盖 / 新增文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R2.md
```

不会覆盖你的长期图谱、Pending、Runtime、快照。

## 新增点

前端“工作事件框架”页新增：

```text
Parser: llm / hybrid / rule
Model: qwen2.5
Timeout seconds
```

默认使用：

```text
llm
qwen2.5
90s
```

## 后端行为

`POST /working/event-frame` 现在默认会调用 Ollama/LangChain：

```text
llm_event_frame_extract()
```

LLM 输出不是聊天回复，而是结构化 EventFrame：

```text
event_kind
summary
importance
slots
candidate_nodes
candidate_edges
uncertainties
```

后端再把它转成统一图谱 delta：

```text
EventFrame node
Slot nodes
Slot --mapsTo--> entity/concept/action
valuable candidate nodes
valuable candidate edges
```

这些都只进入 Working，不直接污染长期图谱。

## 使用

解压到：

```text
E:\Utopia
```

覆盖同名文件，重启后端：

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

Parser 选：

```text
llm
```

点：

```text
解析为工作事件框架
```

Working JSON 里应该看到：

```text
extractor: llm_event_frame:qwen2.5
candidate_event_frames
slots
Name_Haru
Companion_Self --hasAttribute--> Name_Haru
```

如果 LLM 失败，会在 LLM Monitor 里看到原因；如果 fallback 开启，会退回规则事件框架。
