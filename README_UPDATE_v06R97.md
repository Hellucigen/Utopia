# Fascinator v0.6R.9.7 Illocution Pipeline Update

这一版按你的新设计改自然语言处理：

自然语言输入 → 五大言外行为分类 → 激活 Illocution 节点 → jieba/正则分词 → token 匹配节点与边 → 扩散到动作节点 → 执行动作。

## 新增

- 删除旧预设节点：POST /admin/remove-previous-presets
- 写入五大言外行为节点：POST /graph/seed-illocution
- 五大节点：
  - Illocution_Assertive
  - Illocution_Directive
  - Illocution_Commissive
  - Illocution_Expressive
  - Illocution_Declarative
- 动作节点：
  - Action_Answer_From_TopK
  - Action_Write_Graph_Knowledge
  - Action_Graph_Command
  - Action_Ignore_Or_Acknowledge

## 自动 Working + Pending

断言/宣告/承诺类输入会自动生成 Working 与 Pending，但不会直接写入长期图谱，需要审核 commit。

## self 属性

Pending 节点编辑器增加“self 属性节点（维持基线激活）”。

提交后 attributes.is_self=true 的节点会维持 selfBaselineActivation=0.18。

## 覆盖文件

- backend/main.py
- backend/data/schema_registry.json
- backend/data/core_seed_graph.json
- frontend/index.html
- README_UPDATE_v06R97.md

不包含 knowledge_graph.json，不会覆盖长期图谱。

## 使用

覆盖到 E:\Utopia 后重启后端：

```powershell
cd E:\Utopia
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

前端建议换端口：

```powershell
cd E:\Utopia\frontend
py -m http.server 5178 --bind 127.0.0.1
```

打开：

http://127.0.0.1:5178/index.html

## 建议操作

1. 删除旧预设节点
2. 写入五大言外行为节点
3. 测：你的名字是Haru
4. 审核 Pending，可勾选 self
5. commit
6. 测：你的名字是什么
