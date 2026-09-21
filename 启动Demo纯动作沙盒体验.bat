@echo off
chcp 65001 > nul
title Aster 角色运动沙盒 (Demo 原生架构)
cd /d "C:\Users\TimeCraker\.gemini\antigravity\scratch\godot_character_demo"
echo =======================================================
echo   正在启动 Aster 角色纯运动体验沙盒 (46 原生动作)...
echo   - WASD: 基础移动
echo   - Shift: 冲刺
echo   - Space: 跳跃 / 落地缓冲
echo   - 鼠标左键: 挥拳 / 攻击
echo   - ESC: 释放鼠标光标
echo =======================================================
start "" "C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64.exe" --path "C:\Users\TimeCraker\.gemini\antigravity\scratch\godot_character_demo" scenes/main_aster.tscn
