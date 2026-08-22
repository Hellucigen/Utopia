# Fascinator v0.6R.9.6.5 Question route fallback fix

你看到的 JSON 说明你触发的是 Working 解析链路，而不是回答链路。  
更深层的问题是：如果图谱里的 Intent/Action 预置边缺失，系统选中了：

```text
Intent_Directive_Inquiry
```

但解析 Action 时 fallback 错误地退回到：

```text
Action_Write_Working_Memory
```

所以询问句也会进 Working。

## 修复

现在 fallback 会尊重已经选中的 Intent：

```text
Intent_Directive_Inquiry -> Action_Answer_From_TopK
Intent_Graph_Governance_Command -> Action_Graph_Governance
Intent_Assertion / Intent_Preference / Intent_Goal / Intent_Knowledge_Teaching -> Action_Write_Working_Memory
```

所以：

```text
你的名字是什么
```

即使图谱预置边缺失，也会走：

```text
Intent_Directive_Inquiry
Action_Answer_From_TopK
ResponseMode_Concise_First_Person
```

并显示在“回复框”。

## 注意

“强制解析为 Working 记忆（调试）”按钮就是会强行走 Working，用来检查抽取器。  
正常使用请点：

```text
处理输入
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R965.md
```

## 验收

1. 用“处理输入”输入：

```text
你的名字是什么
```

应进入回复框。

2. 用“强制解析为 Working 记忆（调试）”输入同一句，不应再出现：

```text
Name_什么
```
