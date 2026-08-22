# Fascinator v0.6R.9.2.1 hotfix

修复 v0.6R.9.2 中 `/intent/options` 报 Internal Server Error 的问题。

原因：打包时接口已经加入，但遗漏了这些 helper 函数：

```text
intent_option_graph
route_intent_with_llm
activate_intent_route_selection
repair_misguided_v091_graph_nodes
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R921.md
```

## 使用

覆盖到 `E:\Utopia` 后重启后端：

```powershell
cd E:\Utopia
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

然后测试：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/intent/options" -Method Get
```
