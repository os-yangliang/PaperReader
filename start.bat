@echo off
chcp 65001 >nul
echo ========================================
echo    论文阅读助手 - 一键启动
echo ========================================
echo.

REM 启动 API 服务器
start "API Server" cmd /k "cd /d %~dp0 && python -m uvicorn api:app --host 0.0.0.0 --port 8000"

REM 等待 API 服务器启动
timeout /t 3 /nobreak >nul

REM 启动前端开发服务器
start "Frontend Dev" cmd /k "cd /d %~dp0\frontend && npm install && npm run dev"

echo.
echo 服务正在启动...
echo.
echo API 服务器: http://localhost:8000
echo 前端界面:   http://localhost:3000
echo API 文档:   http://localhost:8000/docs
echo.
echo 按任意键打开浏览器...
pause >nul

start http://localhost:3000

