# 白、橙、紫三角色交付

这批角色以用户的九件 GLB 为输入，在 Blender 中装配、绑定并烘焙动作，导入正式 Godot v2 工程的可操作测试场景。源部件保留，装配清单记录真实部件对应关系。

## 直接查看和操作

在工作区根目录双击 `启动三角色动作测试.bat`。首次运行需等待 Godot 导入模型。测试入口为 `client-godot-v2/scenes/character_lab/character_lab.tscn`。

| 操作 | 按键 |
| --- | --- |
| 切换白 / 橙 / 紫 | 1 / 2 / 3 |
| 移动、跑步 | WASD、按住 Shift |
| 跳跃、攻击动作 | 空格、鼠标左键 |
| 交谈展示动作 | E |
| 环绕、缩放 | 按住鼠标右键拖动、滚轮 |
| 原材质 / 基础 Toon 对比 | T |
| 当前角色复位 | R |

身体、服装、头发分别保留网格，共用一套骨架。Godot GLB 中有 26 个变形骨；Blender 工程另有非变形 root，共 27 个。主体骨覆盖躯干、四肢、脚和头；辅助骨覆盖头发、左右衣摆。每个顶点最多四个归一化骨影响。

可编辑工程为 `white/white_master.blend`、`orange/orange_master.blend`、`purple/purple_master.blend`。打开后默认显示 Idle；在动作编辑器可切换 Idle、Walk、Run、Sprint、Jump、Fall、Land、Attack、Talk。动作已烘焙，游戏运行时无需 Blender。

## 交付和验证文件

[检查记录](rigging-review/acceptance.md) 汇总实际通过的检查、具体画面问题和当前适用范围。

- `client-godot-v2/models/characters/*.glb`：游戏内使用的模型、嵌入纹理和九段动作。
- `rigging-review/`：装配和动作图、游戏截图、GLB 检查报告、输入哈希与变形抽查报告。
- `scripts/pipeline/characters/characters.json`：来源映射、比例与装配位置。橙色的原文件名把衣服和头发写反，清单按实际内容纠正。
- `animation-source/`：Quaternius Standard 免费动作源及 CC0 许可。作者说明：[Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html)。使用包内实际存在的动作；Attack 使用 Punch_Jab 直拳，测试场中暂未接武器或命中伤害。

结构检查覆盖全部三件网格的蒙皮、权重和休止变换，以及每段动作的有效变化轨道。Blender 变形检查在九段动作各取七个时间点，报告过度拉伸边，帮助定位精修区域；它不计算全身穿模，也不能替代美术终审。Godot 实机检查在 Forward+ 中运行，记录三人骨架、动作、移动距离、跳跃高度和截图对应的播放状态。

## 当前适用范围

这一版提供可运行的人形动作基础和可编辑工程。露肩皮肤、手腕与袖口、长发和衣摆已作装配及分区权重处理。AI 源网格仍包含碎片、薄片和不规则接缝，极限抬臂、深屈膝时仍需按截图继续精修。长发和衣摆辅助骨具备后续物理驱动入口；当前衣摆使用保守腿部跟随，头发没有物理碰撞。

手部使用整只手骨，尚无逐指控制；没有新建表情形态键。测试场中的 Toon 是材质对比起点。最终脸部光照、描边、发丝高光、布料物理、完整战斗招式和性能档位仍按项目高质量美术目标制作和验收。

当前测试场是正式客户端中的独立场景。原战斗关卡的角色控制、武器挂点和技能状态机需要以这批骨架另做适配，不能因实验场能移动而宣称原战斗系统已经完成替换。

移动速度按脚部支撑阶段的动作步幅抽查设置：走路约 1.03 m/s，跑步约 5.5 m/s。转向、坡地贴脚和脚底锁定尚未使用 IK，需在实际关卡中继续验证。

## 重建流程

已实测工具：Blender 5.2.1 LTS、Godot 4.7.2 stable。完整重建脚本使用 Blender 自带 Python 和 NumPy；单独用系统 Python 执行 GLB 结构检查时需要 NumPy。

运行 `scripts/pipeline/characters/build_all.ps1` 可以重新生成装配工程、绑定工程、GLB 和审查图。它从本机命令解析 Blender，也支持 `-BlenderPath`；输入位置可用 `-SourceRoot` 指定。默认写到系统临时目录中的新文件夹，审查图确认后再替换交付资产。

```powershell
& .\asternova\scripts\pipeline\characters\build_all.ps1 -SourceRoot 'C:\Users\TimeCraker\Pictures\游戏人物建模参考'
python .\asternova\scripts\pipeline\characters\validate_glb.py '<生成目录>\rigged' --report '<生成目录>\glb_validation.json'
```

游戏内自动验证使用 `--verify-characters` 和 `--evidence=<绝对目录>` 两个用户参数，保存真实画面后退出。参考图与渲染图的对照用于观察比例、服装和发型差异；原参考图是 2D 绘画，光照与渲染条件不同，不据此自报相似度。
