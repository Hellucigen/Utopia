# Standalone repair for Fascinator v0.6R.9.1 noisy nodes

把 `REPAIR_V091_GRAPH.py` 放到 `E:\Utopia` 目录下运行：

```powershell
cd E:\Utopia
python .\REPAIR_V091_GRAPH.py
```

它会自动备份：

```text
backend/data/knowledge_graph.json
```

然后删除 v0.6R.9.1 误加的 `Parse_*` / `Answer_*` 节点及其相连边。
