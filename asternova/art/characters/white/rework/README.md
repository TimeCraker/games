# 白色角色返工工程：制作中，未通过美术验收

2026-10-01。制作源为 `white_rework_working.blend`，纹理已打包。`white_static_master.blend` 是用户否定的短发加后发試验，仅作历史比较，禁止用它覆盖新版。

## 当前变化

- 完整独立长发以发冠、后发变形笼分别适配，原短发可恢复隐藏。
- 保留原始脸部，修复后脑重复五官并分离头部表面；眉额贴图线和眼神仍需精修。
- 撤下圆筒手臂，恢复源身体连续肩肘表面；独立原手套按实际腕位装配，新袖筒按手臂重新适配。
- Blender 原生 Cloth 制作静态袖褶，工作袖保留为可编辑网格；此项不等于运行时布料模拟。
- 独立四边面夹克衣片、长衣摆和衬层替换破碎生成衣片；原件可恢复，图案和扣带细节尚未完成。
- 分离腿部表面并平滑，派生短裤重新缝制整齐下摆，原始身体保留。

活动 Blender 通过本机插件 socket 编辑，使用 `blender_live.py` 桥接。当前 Codex 没有原生 Blender MCP 工具，未使用桌面鼠标控制；连接、活动场景编辑和截图已实际验证。

## 结构

`EXPORT_White` 是当前工作对象；`SOURCE_ARCHIVE` 保留源部件，`REJECTED_ASSEMBLY` 保留撤下的试验，`AUTHOR_ClothSimulation` 保留袖褶制作网格。隐藏对象不参与导出。制作源可以继续编辑，导出不从旧参数重建几何。

## 查看与导出

双击 games 根目录 `启动白色静态样板.bat`：1 新版、2 旧版休止、3 旧版 Idle。V 正侧背、H 头部、M 中性材质、P 转台、N 切换 Toon/PBR；右键环绕、滚轮缩放。

```powershell
& 'C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe' -b --python-exit-code 1 -P .\asternova\scripts\pipeline\characters\export_static_review.py -- --blend .\asternova\art\characters\white\rework\white_rework_working.blend --output .\asternova\client-godot-v2\models\characters\rework\white_static.glb
```

命令从 games 根目录运行。导出读取成品、不保存制作源；临时转换拉链/包边曲线，排除隐藏试验。GLB 旁的 `.export.json` 记录制作源与输出哈希，标记 `art_approved=false`。

## 未完成

脸部气质、发夹、蓝黑衣片图形和扣带层次仍与海报有差距。继续检查头发与衣领、袖口、衣摆及腿部穿插。当前预览支持原导入材质和 Godot 原生 Toon 对照；Toon 面部采用平光观察源五官，尚未实现 SDF 面部及完整 NPR 呈现。原材质保留，可随时切换。

`review/poster_old_current.png` 是海报、旧版休止与当前引擎截图对照。`review/godot/` 包含正侧背、脸部、素模、Toon/PBR 和旧版截图；报告明确美术未通过。旧版/新版使用同一相机和灯光，材质与造型属于各自版本；海报透视和姿态不同。旧临时试验图移到 OS temp 历史目录，当前 `review/` 只保留本检查点证据。

宏观进度仍为 2/6。白色静态外观达标并获用户确认后，才扩展紫色、橙色和绑定。本工程没有新版骨架和游戏动作；截图、导出及引擎载入不等于美术验收。
