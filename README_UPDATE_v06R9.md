# Fascinator v0.6R.9 Graph Governance + Natural Language Graph Commands

这一版增加“图谱治理层”，重点不是聊天，而是防止图谱越学越乱。

## 新增程序性记忆节点

覆盖后，前端点一次：

```text
写入预置核心节点
```

会补入：

```text
Graph_Governance_Layer
Merge_Nodes
Rename_Node
Delete_Node
Query_Node_Facts
Health_Check_Graph
Normalize_Relations
```

以及：

```text
Companion_Self --uses--> Graph_Governance_Layer
Graph_Instruction_Layer --routes_to--> Graph_Governance_Layer
Graph_Governance_Layer --uses--> Merge_Nodes
Graph_Governance_Layer --uses--> Rename_Node
Graph_Governance_Layer --uses--> Delete_Node
Graph_Governance_Layer --uses--> Query_Node_Facts
Graph_Governance_Layer --uses--> Health_Check_Graph
Graph_Governance_Layer --uses--> Normalize_Relations
```

## 新增后端接口

```text
POST /nodes/merge
GET  /governance/health
POST /governance/normalize-relations
POST /governance/command
```

## 支持的自然语言图谱指令

### 1. 合并节点

```text
把 Topic_意大利黑帮 合并到 Topic_意大利黑手党
```

解析为：

```json
{
  "command": "merge_nodes",
  "source_id": "Topic_意大利黑帮",
  "target_id": "Topic_意大利黑手党"
}
```

执行后：

```text
source 所有入边迁移到 target
source 所有出边迁移到 target
重复边去重
source 可保留为 alias 节点
activation 迁移到 target
```

### 2. 重命名节点

```text
把 Name_Haru 重命名为 Name_Haru_Main
```

等价于已有重命名功能。

### 3. 删除节点

```text
删除节点 Topic_xxx
```

会删除该节点和所有相连边。

### 4. 查询节点相关事实

```text
查询 Companion_Self 相关事实
```

返回 `recall_node` 的局部事实。

### 5. 列出某类关系边

```text
列出所有 name_is 边
```

返回所有该 relation 的边。

### 6. 健康检查

```text
图谱健康检查
```

检查：

```text
孤立节点
重复边
坏边 endpoint
低权重节点
Name_/Topic_/Goal_/Relationship_ 缺少 value 的节点
疑似重复节点
事件节点数量
```

### 7. 关系规范化

```text
关系规范化
```

会把常见变体统一，比如：

```text
is_interested_in -> interested_in
has_interest_in -> interested_in
has_name -> name_is
called -> name_is
```

## 前端新增页面

```text
图谱治理
```

包含：

```text
自然语言图谱指令解析/执行
手动合并节点
图谱健康检查
关系规范化
```

建议破坏性操作先点：

```text
解析预览
```

确认无误再执行。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
backend/data/core_seed_graph.json
frontend/index.html
README_UPDATE_v06R9.md
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

## 推荐验收

1. 点“写入预置核心节点”
2. 打开“图谱治理”
3. 点“图谱健康检查”
4. 测试解析：

```text
把 Topic_意大利黑帮 合并到 Topic_意大利黑手党
```

5. 如果图谱中确实有这两个节点，再执行合并。
6. 查询：

```text
查询 Companion_Self 相关事实
```

7. 列出：

```text
列出所有 name_is 边
```

验收完成后创建快照：

```text
v0.6R9_graph_governance_success
```
