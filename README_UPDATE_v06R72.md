# Fascinator v0.6R.7.2 Graph UX + JSON Graph Language

这版修复你刚刚看到的重复事实，并增强图谱 UI。

## 1. 修复“意大利黑帮 / 意大利黑手党”重复问题

v0.6R.7.1 中，LLM 抽出了：

```text
User --interested_in--> Topic_意大利黑帮
```

同时 rule_repair 从原文抽出了：

```text
User --interested_in--> Topic_意大利黑手党
```

这版规则：

```text
如果 rule_repair 已经从原文识别出同一 src + relation 的精确事实，
则忽略 LLM 的同类泛化事实。
```

所以：

```text
我对意大利黑手党很感兴趣
```

应该只保留：

```text
User --interested_in--> Topic_意大利黑手党
```

## 2. 主图支持拖动、缩放、节点拖拽

主图新增：

```text
鼠标滚轮缩放
拖动空白区域平移
拖动节点调整位置
重置视图
```

节点位置目前是前端临时布局，不写入后端。

## 3. 激活运行时点击节点自动选中

现在点击主图/Top-k 里的节点，会自动填入：

```text
Seed IDs
Recall Node ID
Graph Edit Node ID
```

方便继续注入激活或查询回忆。

## 4. JSON Graph Language

新增后端接口：

```text
POST /graph/import-json
```

支持三种输入：

### facts 简写

```json
{
  "facts": [
    {
      "src": "User",
      "relation": "currently_learning",
      "dst": "Topic_强化学习",
      "weight": 0.85,
      "attributes": {
        "source": "manual_json"
      }
    }
  ]
}
```

### nodes / edges

```json
{
  "nodes": [
    {
      "id": "Robot",
      "kind": "declarative",
      "tau": "semantic",
      "weight": 0.8,
      "attributes": {}
    }
  ],
  "edges": [
    {
      "src": "Robot",
      "relation": "has",
      "dst": "Sensor",
      "weight": 0.85,
      "attributes": {}
    }
  ]
}
```

### candidate_nodes / candidate_edges

兼容 Pending delta 格式。

前端新增：

```text
JSON组织图谱
```

可选择：

```text
生成 Pending
直接写入图谱
```

建议默认用“生成 Pending”。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R72.md
PROMPT_DAILY_KNOWLEDGE_GENERATOR.md
```

## 使用

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

## 测试

```text
我对意大利黑手党很感兴趣
```

理想结果只出现：

```text
User --interested_in--> Topic_意大利黑手党
```

不应该再同时出现：

```text
Topic_意大利黑帮
```
