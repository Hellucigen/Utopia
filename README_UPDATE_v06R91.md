# Fascinator v0.6R.9.1 Parse Nodes + Answer Mode Nodes

这一版不改主要后端逻辑，主要给系统预置更多“输入解析类型节点”和“回答方式节点”，方便后续把 Haru 的语用识别和输出选择做成图谱内的程序性记忆，而不是一堆散乱 if-else。

## 使用

覆盖后重启，然后前端点一次：

```text
写入预置核心节点
```

会补入本版新增节点和边。

## 新增输入解析类型节点

```text
Input_Pragmatics_Layer
Parse_Assertion_Input
Parse_Directive_Inquiry
Parse_Command_Input
Parse_Feedback_Input
Parse_Correction_Input
Parse_Preference_Input
Parse_Goal_Input
Parse_Knowledge_Teaching_Input
Parse_Self_Reference_Input
Parse_User_State_Input
Parse_Low_Value_Input
```

它们都是：

```text
kind=procedural
tau=procedural
```

### 设计意图

用户输入先经过：

```text
Parse_User_Stimulus --routes_to--> Input_Pragmatics_Layer
```

再分类到：

```text
Input_Pragmatics_Layer --classifies_to--> Parse_Directive_Inquiry
Input_Pragmatics_Layer --classifies_to--> Parse_Assertion_Input
...
```

例如：

```text
Haru现在知道自己叫什么吗？
```

对应：

```text
Parse_Directive_Inquiry
```

然后：

```text
Parse_Directive_Inquiry --routes_to--> Answer_Directive_Inquiry_From_TopK
```

## 新增回答方式节点

```text
Response_Generation_Layer
Answer_Concise_First_Person
Answer_With_Evidence_Edge
Answer_Debug_Context
Answer_Insufficient_Context
Answer_Clarifying_Question
Answer_Teaching_Mode
Answer_Reflective_Companion
Answer_Governance_Result
Answer_Recall_Summary
Answer_Action_Confirmation
```

### 设计意图

回答生成先经过：

```text
Answer_Directive_Inquiry_From_TopK --uses--> Response_Generation_Layer
```

再选择回答模式：

```text
Response_Generation_Layer --selects_mode--> Answer_Concise_First_Person
Response_Generation_Layer --selects_mode--> Answer_With_Evidence_Edge
Response_Generation_Layer --selects_mode--> Answer_Insufficient_Context
...
```

目前 v0.6R.8.3 的真实回答逻辑仍然主要走 `Answer_Directive_Inquiry_From_TopK`，但这些节点会进入图谱，作为后续 v0.7 多回答策略的结构基础。

## 推荐观察

写入后打开主图，应该看到两个新的程序性区域：

```text
Input_Pragmatics_Layer
Response_Generation_Layer
```

它们会把输入解析与输出方式从代码模块逐渐迁移到图谱内的程序性记忆结构。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
backend/data/core_seed_graph.json
frontend/index.html
README_UPDATE_v06R91.md
```
