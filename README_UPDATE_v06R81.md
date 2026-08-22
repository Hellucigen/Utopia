# Fascinator v0.6R.8.1 Query Activation Before Answer

你指出得对：如果要“基于 Top-k 回复”，不能直接拿旧 Top-k。必须先让自然语言问题激活相关节点，再扩散，形成新的 Top-k，然后回答。

## 新回答链路

```text
用户询问
→ 判断是否是指令类询问句
→ 从问题文本解析/匹配相关图谱节点
→ 对这些节点注入 activation
→ 扩散 N 次
→ 生成新的 Top-k
→ 收集 Top-k 节点及相连边
→ 输入 LLM
→ 输出回答
```

## 新增程序性记忆节点

覆盖后点一次：

```text
写入预置核心节点
```

会补入：

```text
Infer_Query_Seed_Nodes
Activate_Query_Seeds
```

以及：

```text
Answer_Directive_Inquiry_From_TopK --uses--> Infer_Query_Seed_Nodes
Infer_Query_Seed_Nodes --uses--> Activate_Query_Seeds
Activate_Query_Seeds --precedes--> Recall_TopK_Context
```

## 后端变化

`POST /qa/answer` 新增参数：

```json
{
  "question": "Haru现在知道自己叫什么吗？",
  "auto_activate": true,
  "spread_steps": 3,
  "seed_value": 1.0
}
```

返回的 `context.query_activation` 会显示：

```json
{
  "seed_nodes": ["Companion_Self", "Name_Haru"],
  "spread_steps": 3
}
```

## 前端变化

“询问回答输出”页面新增：

```text
Auto activate from question
Spread steps after query activation
Seed value
```

回答结果会显示本次从问题中解析出的 seed nodes。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
backend/data/core_seed_graph.json
frontend/index.html
README_UPDATE_v06R81.md
```

## 使用

覆盖到：

```text
E:\Utopia
```

重启后端：

```powershell
cd E:\Utopia
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

前端 Ctrl + F5。

## 测试

不用手动先注入了，可以直接问：

```text
Haru 现在知道自己叫什么吗？
```

理想 query_activation 里会出现：

```text
Companion_Self
Name_Haru
```

然后回答会基于：

```text
Companion_Self --name_is--> Name_Haru
```

同理：

```text
根据当前图谱，用户是谁？
根据当前图谱，Robot 是什么？
```
