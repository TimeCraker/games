# 白色角色装配交接：原资产细节候选

更新：2026-10-01 晚。此文为实际检查点，不是美术验收结论。

## 边界与来源

白色静态样板获得用户确认之前，不制作紫色、橙色或绑定。当前进度 3/6，仅增加勾选已完成的导出、引擎运行和证据交付。

- 原始资产：`C:\Users\TimeCraker\Pictures\游戏人物建模参考`，三件白色原始 GLB 未修改。
- 海报：`白色/海报参考图/01_主选海报参考图_厚底战术靴版.jpg`。
- 唯一制作源：`asternova/art/characters/white/rework/white_rework_working.blend`。
- 运行资源：`asternova/client-godot-v2/models/characters/rework/white_static.glb`。
- `white_static_master.blend` 及旧脚本参数均不能用于覆盖当前工作源。

## 本次保留的变化

1. 保留 `Head_Work` 原五官，头部坐标、面索引及 UV 哈希与 `Head_BeforeForeheadCleanup` 一致。新增 `Head_ScalpClosure` 补开放的头顶/后脑，并按头发表面内侧限制外形。
2. 当前头发是 `Hair_ScalpFit_Work`。继承此前完整长发的求值网格；仅保留一个新贴合笼 `ScalpLandmarks_Cage`。新增刘海、发冠、侧发、后发编辑组。旧 `Hair_Full_Work` 隐藏保留。发夹以中心随贴合笼移位，形状不变。
3. 衣服改用从 `Outfit_Raw` 派生的 `Outfit_SourceDetail_Work`，恢复原袖褶、衣片、腰带、衣摆图形和手套。左右袖子分别对齐手臂与手腕，领口降低。变形选择按连通部件排除腰腿附件。
4. 服装重复点焊接后重算法线；隐藏部分肩部独立碎片。袖内身体用可恢复 MASK，前臂仍保留。新袖口为 `SleeveCuff_Fitted_-1/1`。
5. 旧硬片衣片、简化衣摆与袖筒隐藏归档。导出集合当前 13 个网格，0 蒙皮、0 动作。

## 未保留的试验

新的光滑条带刘海丢失原造型且露出切口；强行推入额头和单向 Shrinkwrap 造成穿插/折面；脸部法线重算没有改善；新增肩板悬空。均已撤下，生产文件没有采用这些结果。不能把这些临时脚本当作新生成入口。

Blender 的 5 点 Lattice 默认坐标范围为 -2 到 2；新笼尺寸已按实测坐标设置，不能假定始终为 -0.5 到 0.5。

## 继续工作重点

服装的原设计层次比接手时更完整，但最终静态验收仍未完成。头部收拢幅度有限；肩部仍有源网格/贴图造成的破碎感，耳周细节、脸部烘焙阴影和局部接缝需继续检查。不能宣称完全无穿插或已达到海报品质。

先查看最新对照，保留原眉眼；如继续修改头发，优先在已有编辑组中处理实际发束与内腔，不叠加整件缩放。服装保留本次恢复的原褶皱，不再换回大面积硬片。每轮修改后立即看正侧背图，只有保留的修改才保存至 working blend。

## 最新证据

`asternova/art/characters/white/rework/review/`：

- `source_detail_comparison.png`：海报、24480d8 时的模型、当前模型。
- `source_detail_head_comparison.png`：同相机头部前后正侧面对照。
- `source_detail_assembly/`：当前全身、头部、中性材质，`render_report.json` 和 `structure_report.json`。
- `godot/`：已更新的实际引擎多视图。报告 13 个网格、10 张图全部保存成功、`art_approved=false`。

旧 `checkpoint_*`、`hair_fit_*`、`poster_old_current.png` 及旧测量报告是历史证据，不代表当前模型。

## 工具与命令

本轮实际使用活动 Blender MCP 插件的 socket，桥接为 `scripts/pipeline/characters/blender_live.py`，不是 Codex 原生注册的 Blender MCP。活动窗口关闭过一次，后来从已记录操作恢复候选并保存；当前磁盘 working blend 是最终保留结果。Computer Use 实际用于恢复被最小化的 Godot，自动截图随后完成并正常退出。

Blender：`C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe`。
Godot：`C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe`。

从 games 根目录按顺序执行并等待退出：

```powershell
& 'C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe' -b --python-exit-code 1 -P .\asternova\scripts\pipeline\characters\export_static_review.py -- --blend .\asternova\art\characters\white\rework\white_rework_working.blend --output .\asternova\client-godot-v2\models\characters\rework\white_static.glb

& 'C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe' -b --python-exit-code 1 -P .\asternova\scripts\pipeline\characters\render_static_review.py -- --blend .\asternova\art\characters\white\rework\white_rework_working.blend --output .\asternova\art\characters\white\rework\review\source_detail_assembly

& 'C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe' --headless --path .\asternova\client-godot-v2 --editor --import --quit

& 'C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe' --path .\asternova\client-godot-v2 --resolution 1280x900 res://scenes/character_lab/white_static_review.tscn -- --verify-white-static --evidence=C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/characters/white/rework/review/godot
```

不要最小化正在截图的 Godot，否则可能等待 `frame_post_draw`。渲染器和导出器只读源文件；重新导出后须核对哈希并更新结构报告。没有测量帧时，不宣称 120 FPS。
