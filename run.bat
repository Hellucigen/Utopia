@echo off
echo 正在启动 Utopia 项目...

:: 修改后的后端启动命令
echo 正在启动后端 (Uvicorn)...
start "Utopia-Backend" cmd /k "cd /d E:\Utopia && PowerShell.exe -NoProfile -ExecutionPolicy Bypass -Command ".\.venv\Scripts\Activate.ps1; python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000""

:: 前端保持不变
echo 正在启动前端 (http.server)...
start "Utopia-Frontend" cmd /k "cd /d E:\Utopia\frontend && py -m http.server 5174 --bind 127.0.0.1"

echo 启动指令已发送。