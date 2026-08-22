# Fascinator v0.6R.9.2 LLM Intent Router + Graph Repair

这一版修正 v0.6R.9.1 的误解：不是单纯堆“解析节点/回答节点”，而是让 LLM 看到所有意图节点，然后选择一个意图节点激活，再由图谱决定行动和回答方式。

## 1. 图谱修复

v0.6R.9.1 添加了过多 `Parse_*` / `Answer_*` 节点，容易把图谱弄乱。  
本版新增清理接口：

```text
POST /governance/repair-v091
```

前端在：

```text
图谱治理 → 清理 v0.6R.9.1 误加节点
```

点击后会删除这些误加节点及其相连边：

```text
Input_Pragmatics_Layer
Parse_Assertion_Input
Parse_Directive_Inquiry
...
Response_Generation_Layer
Answer_Concise_First_Person
Answer_Debug_Context
...
```

不会删除你原本的核心节点，比如：

```text
Answer_Directive_Inquiry_From_TopK
Graph_Governance_Layer
Companion_Self
User
```

## 2. 新的意图路由结构

新增三类节点：

### Intent_* 意图节点

```text
Intent_Assertion
Intent_Directive_Inquiry
Intent_Graph_Governance_Command
Intent_Correction
Intent_Feedback
Intent_Preference
Intent_Goal
Intent_Knowledge_Teaching
Intent_Debug_Request
Intent_Low_Value
```

### Action_* 行动节点

```text
Action_Write_Working_Memory
Action_Answer_From_TopK
Action_Graph_Governance
Action_Show_Debug_Context
Action_Ask_Clarification
Action_Ignore_Low_Value
Action_Update_Response_Preference
```

### ResponseMode_* 回答方式节点

```text
ResponseMode_Concise_First_Person
ResponseMode_Evidence_Brief
ResponseMode_Debug
ResponseMode_Clarifying
ResponseMode_Governance_Result
ResponseMode_Teaching
ResponseMode_Insufficient_Context
```

## 3. LLM 如何选择

新增接口：

```text
GET /intent/options
POST /intent/route
```

`/intent/route` 会把当前图谱中的所有：

```text
Intent_*
Action_*
ResponseMode_*
```

节点和它们的连接一起输入 LLM，让 LLM 选择：

```json
{
  "selected_intent_id": "Intent_Directive_Inquiry",
  "selected_action_id": "Action_Answer_From_TopK",
  "selected_response_mode_id": "ResponseMode_Concise_First_Person"
}
```

然后系统会激活这些节点。

## 4. 回答流程变化

`/qa/answer` 现在也会先走意图路由：

```text
用户输入
→ 所有 Intent_* 节点输入 LLM
→ LLM 选择一个 Intent_*
→ 激活 Intent / Action / ResponseMode
→ 再解析问题中的实体节点
→ 扩散
→ Top-k
→ LLM 基于 Top-k 和选中的回答方式输出
```

这样不是固定“询问就回答”，而是从图谱内的意图节点中选择路径。

## 5. 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
backend/data/core_seed_graph.json
frontend/index.html
README_UPDATE_v06R92.md
```

## 6. 使用

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

然后执行：

```text
1. 点“写入预置核心节点”
2. 打开“图谱治理”
3. 点“清理 v0.6R.9.1 误加节点”
4. 打开“意图路由”
5. 测试：
   - Haru现在知道自己叫什么吗？
   - 把 Topic_意大利黑帮 合并到 Topic_意大利黑手党
   - 我最近在学强化学习
```

## 7. 验收目标

对于：

```text
Haru现在知道自己叫什么吗？
```

意图路由应该接近：

```text
Intent_Directive_Inquiry
Action_Answer_From_TopK
ResponseMode_Concise_First_Person
```

对于：

```text
把 Topic_意大利黑帮 合并到 Topic_意大利黑手党
```

意图路由应该接近：

```text
Intent_Graph_Governance_Command
Action_Graph_Governance
ResponseMode_Governance_Result
```
