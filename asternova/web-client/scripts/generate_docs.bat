@echo off
chcp 65001 >nul
title AsterNova Frontend Doc Generator
echo 正在启动前端项目文档生成脚本...
echo.

:: 以绕过执行策略的方式运行同目录下的 ps1 脚本
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0generate_docs.ps1"

echo.
pause