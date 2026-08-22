# Fascinator v0.6R.9.6.2 frontend dead-buttons hotfix

修复“所有按钮没反应”的问题。

原因：v0.6R.9.6.1 的 `frontend/index.html` 里同时出现了：

```javascript
var selectedEdgeId = "";
let selectedEdgeId = "";
```

浏览器会直接抛出 SyntaxError，导致整段前端 JS 不执行，所以所有按钮都没反应。

本版修复：

```text
1. selectedEdgeId 只声明一次
2. 前端 normalizeClientGraph()，避免坏 graph payload 让 UI 崩掉
3. 后端 graph() 对 nodes/edges 做类型修正
4. 本更新包不包含 backend/data/knowledge_graph.json，避免再次覆盖你的图谱数据
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R962.md
```

## 使用

覆盖到 E:\Utopia 后重启后端：

```powershell
cd E:\Utopia
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

前端建议换端口绕开缓存：

```powershell
cd E:\Utopia\frontend
py -m http.server 5176 --bind 127.0.0.1
```

打开：

```text
http://127.0.0.1:5176/index.html
```

然后点“同步”和“导入预置核心节点”。
