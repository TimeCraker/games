@echo off
chcp 65001 > nul
title AsterNova - 核心战斗与高机动身法体验 (Aster 真身实装)
cd /d "%~dp0asternova\client-godot-v2"
echo =======================================================
echo   正在启动 AsterNova 核心战斗原型沙盒 (Aster 角色工业实装)...
echo   - WASD: 移动 (Walk 2.8m/s, Run 7.0m/s)
echo   - Shift: 极限疾跑
echo   - Space: 跳跃 / 二段跳 / 贴墙蹬墙跳
echo   - Ctrl / C: 高速滑铲
echo   - 鼠标左键: 四段挥砍连招 (拔刀出鞘 + 刀光条带 + 单体卡肉)
echo   - 鼠标右键: 蓄力居合疾冲斩 (纳刀蓄势 -> 破空出刀)
echo   - 鼠标中键: 切换 TPP / FPP 视角
echo =======================================================
start "" "C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64.exe" --path "%~dp0asternova\client-godot-v2" scenes/levels/combat_playground.tscn
