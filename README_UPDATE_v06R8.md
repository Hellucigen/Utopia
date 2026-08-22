# Fascinator v0.6R.8 Graph Instruction Layer + Directive Inquiry Answer

这一版增加两个东西：

1. 图谱指令层的预置程序性记忆节点
2. 一个简单的“询问句回答”程序性记忆节点和输出 UI

## 1. 新增程序性记忆节点

覆盖后，前端点一次：

```text
写入预置核心节点
```

会补入：

```text
Graph_Instruction_Layer
Answer_Directive_Inquiry_From_TopK
Recall_TopK_Context
```

以及关系：

```text
Companion_Self --uses--> Graph_Instruction_Layer
Graph_Instruction_Layer --routes_to--> Handle_Question
Handle_Question --uses--> Answer_Directive_Inquiry_From_TopK
Answer_Directive_Inquiry_From_TopK --uses--> Recall_TopK_Context
```

节点仍然是：

```text
kind=procedural
tau=procedural
```

## 2. 当前回答能力范围

只处理：

```text
语用学中的指令类询问句
```

例如：

```text
Haru 现在知道自己叫什么吗？
根据当前图谱，用户是谁？
根据当前图谱，Robot 是什么？
告诉我 Companion_Self 相关事实
解释当前 Focus
```

暂时不处理普通命令、闲聊或开放式聊天。

## 3. 回答逻辑

调用：

```text
POST /qa/answer
```

后端会：

```text
读取当前 runtime top_k
收集 top_k 节点
收集与 top_k 相连的边
把这些上下文输入 LLM
LLM 根据图谱上下文输出自然语言答案
```

如果当前 Top-k 没有相关节点，答案应该说上下文不足。

## 4. 前端输出 UI

新增页面：

```text
询问回答输出
```

使用方式：

```text
1. 先去激活运行时
2. Seed IDs 填 Companion_Self / User / Robot
3. 注入
4. Tick 几次
5. 打开“询问回答输出”
6. 输入问题
7. 点“基于当前 Top-k 回答”
```

回答下方会显示本次输入给 LLM 的上下文 JSON。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
backend/data/core_seed_graph.json
frontend/index.html
README_UPDATE_v06R8.md
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

前端：

```text
Ctrl + F5
```

## 推荐测试

### 测 Haru 自认知

```text
清空
Seed IDs: Companion_Self
注入
Tick 3 次
```

然后问：

```text
Haru 现在知道自己叫什么吗？
```

理想回答会基于：

```text
Companion_Self --name_is--> Name_Haru
```

### 测用户身份

```text
清空
Seed IDs: User
注入
Tick 3 次
```

然后问：

```text
根据当前图谱，用户是谁？
```

### 测知识

```text
清空
Seed IDs: Robot
注入
Tick 3 次
```

然后问：

```text
根据当前图谱，Robot 是什么？
```
