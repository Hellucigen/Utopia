# Fascinator v0.6R.7.1 hotfix

修复 v0.6R.7 中构建 Working EventFrame 时报错：

```text
name 'new_run' is not defined
```

原因：v0.6R.7 打包时遗漏了 LLM Monitor 的运行记录 helper：

```text
new_run
run_event
run_update
```

本补丁只恢复这些函数，不改变 v0.6R.7 的通用断言框架逻辑。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R71.md
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
