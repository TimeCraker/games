@echo off
chcp 65001 > nul
title AsterNova 角色与战斗沙盒体验
echo ========================================================
echo   AsterNova 角色与动作沙盒启动中...
echo   角色模型：Tripo 终极母带装配（双腿0撕裂、鞋跟坚挺无损）
echo   步态优化：身法动量挺拔前倾（告别后仰）
echo   佩刀装配：星霜月华零偏置纳刀态 / 手腰双插槽拔刀
echo ========================================================
cd /d "%~dp0client-godot-v2"
start "" "C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe" --path "%~dp0client-godot-v2"
