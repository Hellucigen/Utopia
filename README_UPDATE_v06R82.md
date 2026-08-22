# Fascinator v0.6R.8.2 Companion Answer Style

这一版只优化回答风格，不改主架构。

## 修复目标

v0.6R.8.1 已经能做到：

```text
问题 → 解析 seed nodes → 激活 → 扩散 → Top-k → LLM 回答
```

但回答太像调试报告。  
v0.6R.8.2 改成更像 Haru 的简短第一人称回答。

## 新回答风格

问：

```text
Haru 现在知道自己叫什么吗？
```

理想回答：

```text
我叫 Haru。
```

或者：

```text
知道，我叫 Haru。图谱里有 Companion_Self --name_is--> Name_Haru。
```

## Prompt 约束

新增约束：

```text
默认第一人称
像正在成长的伙伴，不像调试器
优先 1 句，最多 3 句
不输出标题、Markdown、小节、时间戳、激活值、Top-k、Focus、seed nodes
不说“如果还有问题请告诉我”
上下文不足时说“我现在还不能从图谱里确定。”
```

## 后端优化

新增：

```text
graph_answer_hint()
clean_graph_answer_text()
```

其中：

```text
Companion_Self --name_is--> Name_Haru
```

会给 LLM 一个直接提示：

```text
我叫 Haru。
```

如果模型仍然输出冗长答案，后端会做轻量清理，删除套话和过多调试格式。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R82.md
```

## 使用

覆盖到：

```text
E:\Utopia
```

重启：

```powershell
cd E:\Utopia
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

前端 Ctrl + F5。

## 测试

直接问：

```text
Haru 现在知道自己叫什么吗？
```

理想结果类似：

```text
我叫 Haru。
```

如果问：

```text
根据当前图谱，用户是谁？
```

理想结果类似：

```text
你叫 Hellucigen。
```
