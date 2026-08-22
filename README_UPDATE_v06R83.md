# Fascinator v0.6R.8.3 Value-aware Answer + Rename Node

这一版修你刚刚指出的问题：

```text
Companion_Self 的名字是 Name_Haru
```

这不自然。回答时应该使用节点的 `attributes.value`，也就是：

```text
我叫 Haru。
```

## 1. 回答上下文加入 value/display

后端 `topk_context()` 现在会把节点转换成：

```json
{
  "id": "Name_Haru",
  "display": "Haru",
  "attributes": {
    "value": "Haru"
  }
}
```

边也会带自然显示字段：

```json
{
  "src": "Companion_Self",
  "src_display": "Companion Self",
  "relation": "name_is",
  "dst": "Name_Haru",
  "dst_display": "Haru"
}
```

Prompt 新增约束：

```text
优先使用 display/value 字段，不要把原始节点 ID 当成人类可读名字。
```

所以问：

```text
Haru 现在知道自己叫什么吗？
```

理想回答：

```text
我叫 Haru。
```

## 2. 轻量输出清理

如果模型仍然输出：

```text
Name_Haru
Topic_强化学习
Goal_图谱整洁
```

后端会在最终答案中轻量替换为：

```text
Haru
强化学习
图谱整洁
```

## 3. 新增重命名节点功能

后端新增：

```text
POST /nodes/{node_id}/rename
```

请求：

```json
{
  "new_id": "New_Node_ID",
  "keep_old_alias": false
}
```

会做：

```text
旧节点 ID -> 新节点 ID
所有 src=旧ID 的边迁移到新ID
所有 dst=旧ID 的边迁移到新ID
activation 也迁移
```

如果 `keep_old_alias=true`，会保留旧节点作为 alias 节点，并创建：

```text
Old_ID --alias_of--> New_ID
```

## 4. 前端新增重命名 UI

在：

```text
图谱编辑
```

里新增：

```text
Rename selected node to
Keep old alias?
重命名选中节点并迁移边
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R83.md
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

问：

```text
Haru 现在知道自己叫什么吗？
```

理想：

```text
我叫 Haru。
```

或者最多：

```text
知道，我叫 Haru。
```
