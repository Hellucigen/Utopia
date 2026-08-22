# Fascinator v0.6R.9.6.4 Prompt + UI + Graph Surface Update

这一版做三件事：

1. 优化事实抽取 prompt
2. 优化回答 prompt
3. 把“自然语言输入”页面拆成回复框 / Working 生成框 / 图谱治理框

## 1. 抽取 Prompt 优化

修复核心目标：

```text
问题不能被写成事实。
```

尤其是：

```text
你的名字是什么
你叫什么
你叫啥
```

现在 prompt 明确要求：

```text
intent_class = question
facts = []
```

并禁止生成：

```text
Name_什么
Name_啥
Topic_什么
```

对于断言类：

```text
你的名字是Haru
```

才生成：

```text
Companion_Self --name_is--> Name_Haru
```

## 2. 回答 Prompt 优化

回答 prompt 现在会读取：

```text
ResponseMode_*
```

并根据模式调整回答：

```text
ResponseMode_Concise_First_Person
ResponseMode_Evidence_Brief
ResponseMode_Debug
ResponseMode_Teaching
ResponseMode_Governance_Result
```

默认仍然是简短第一人称，例如：

```text
我叫 Haru。
```

## 3. 自然语言输入 UI 拆分

原来所有东西都挤在一个输出框里。

现在分成：

```text
回复框
Working 生成框
图谱治理框
内部处理结果 JSON
```

### 询问类输入

```text
你的名字是什么
```

显示在：

```text
回复框
```

### 断言/教学类输入

```text
你的名字是Haru
我最近在学强化学习
```

显示在：

```text
Working 生成框
```

### 图谱治理类输入

```text
把 Topic_A 合并到 Topic_B
```

显示在：

```text
图谱治理框
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R964.md
```

如果包里包含 `backend/data/core_seed_graph.json`，只影响“导入预置核心节点”，不会覆盖当前长期图谱。

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

前端建议换端口避免缓存：

```powershell
cd E:\Utopia\frontend
py -m http.server 5177 --bind 127.0.0.1
```

打开：

```text
http://127.0.0.1:5177/index.html
```

## 验收

### A. 问题

```text
你的名字是什么
```

应该在“回复框”显示回答，不应该在 Working 里产生 Name_什么。

### B. 断言

```text
你的名字是Haru
```

应该在“Working 生成框”显示候选图谱 delta。

### C. 偏好

```text
我最近在学强化学习
```

应该进入 Working 生成框。

### D. 治理

```text
把 Topic_A 合并到 Topic_B
```

应该进入图谱治理框，默认只预览。
