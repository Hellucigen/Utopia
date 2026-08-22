# Fascinator v0.6R.9.5 Graph-resolved Action Routing

这版修正 v0.6R.9.4 的概念问题。

你说得对：  
`你的名字是Haru` 不应该是“保护一下别误判”，而应该走完整图谱流程：

```text
自然语言输入
→ 解析/选择 Intent_Assertion 节点
→ 激活 Intent_Assertion
→ 通过图谱边 Intent_Assertion --selects_action--> Action_Write_Working_Memory
→ 激活 Action_Write_Working_Memory
→ 把输入提取出的信息送入写入图谱知识的行动
→ 生成 Working/Pending 图谱 delta
```

## 本版核心变化

### 1. 不再由“保护逻辑”直接指定 Action

上一版类似：

```text
看到“你的名字是Haru”
→ 直接 selected_action_id = Action_Write_Working_Memory
```

这不符合你的设计。

现在改为：

```text
rule/LLM 只选择 Intent_*
Action_* 必须从图谱边中解析
ResponseMode_* 也从图谱边中解析
```

也就是：

```text
Intent_* --selects_action--> Action_*
Action_* --uses_response_mode--> ResponseMode_*
```

## 2. 新增内部函数

```text
rule_intent_candidate()
resolve_action_and_response_from_graph()
route_natural_input_to_graph_action()
```

### route_natural_input_to_graph_action

流程：

```text
输入句子
→ rule_intent_candidate 或 LLM route 选择 Intent_*
→ resolve_action_and_response_from_graph 从图谱边找 Action_*
→ 再从 Action_* 边找 ResponseMode_*
```

## 3. 对“你的名字是Haru”的预期

输入：

```text
你的名字是Haru
```

应该得到：

```text
intent = Intent_Assertion
action = Action_Write_Working_Memory
mode = ResponseMode_Concise_First_Person
kind = working_memory
```

Working JSON 里应该有：

```text
Companion_Self --name_is--> Name_Haru
```

## 4. 对询问的预期

输入：

```text
Haru现在知道自己叫什么吗？
```

应该得到：

```text
intent = Intent_Directive_Inquiry
action = Action_Answer_From_TopK
mode = ResponseMode_Concise_First_Person
kind = answer
```

并回答：

```text
我叫 Haru。
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R95.md
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

## 验收

在“自然语言输入”中测试：

```text
你的名字是Haru
```

应该生成 Working 记忆，不应该回答。

再测试：

```text
Haru现在知道自己叫什么吗？
```

才应该回答。
