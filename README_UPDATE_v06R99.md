# Fascinator v0.6R.9.9 Minimal Presets Cleanup

这一版专门修复“预设节点没删干净”的问题。

## 只保留这些预设节点

### 核心身份节点

```text
Companion_Self
User
```

### 五大言外行为节点

```text
Illocution_Assertive
Illocution_Directive
Illocution_Commissive
Illocution_Expressive
Illocution_Declarative
```

### 两个动作节点

```text
Action_Answer_From_TopK
Action_Write_Graph_Knowledge
```

### 超参数 self 节点

```text
Hyperparam_*
```

## 删除这些预设节点

这版会清理掉：

```text
Illocution_Classifier
Action_Graph_Command
Action_Ignore_Or_Acknowledge
Graph_Governance_Layer
Merge_Nodes
Rename_Node
Delete_Node
Query_Node_Facts
Health_Check_Graph
Normalize_Relations
Intent_*
ResponseMode_*
Parse_*
Answer_*
Input_Pragmatics_Layer
Response_Generation_Layer
Select_Response_Box
Select_Working_Box
Extract_Graph_Facts
```

也就是说，整理图谱、治理图谱、图谱命令等之前预设节点都不再保留。

## 自然语言处理仍然可用

分类仍然使用五大言外行为节点的 `value` 与 `prompt`，但不再额外创建 `Illocution_Classifier` 节点。

流程：

```text
自然语言输入
→ LLM/rule 根据五大 Illocution 节点分类
→ 激活对应 Illocution 节点
→ token 匹配节点与边
→ 多轮扩散
→ 选择动作
```

动作只剩两个：

```text
指令类 -> Action_Answer_From_TopK
非指令类 -> Action_Write_Graph_Knowledge
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
backend/data/core_seed_graph.json
frontend/index.html
README_UPDATE_v06R99.md
```

不包含：

```text
knowledge_graph.json
runtime_state.json
```

不会覆盖长期图谱。

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

前端建议换端口：

```powershell
cd E:\Utopia\frontend
py -m http.server 5180 --bind 127.0.0.1
```

打开：

```text
http://127.0.0.1:5180/index.html
```

## 关键操作

进入自然语言输入页，先点：

```text
删除旧预设节点
```

然后点：

```text
写入最小预设节点
```

再到“激活运行时”点：

```text
创建/同步超参数 self 节点
```

## 验收

图谱里不应该再有：

```text
Action_Graph_Command
Action_Ignore_Or_Acknowledge
Illocution_Classifier
Graph_Governance_Layer
Merge_Nodes
Rename_Node
Delete_Node
Intent_*
ResponseMode_*
```

应该只看到：

```text
Companion_Self
User
Illocution_*
Action_Answer_From_TopK
Action_Write_Graph_Knowledge
Hyperparam_*
```
