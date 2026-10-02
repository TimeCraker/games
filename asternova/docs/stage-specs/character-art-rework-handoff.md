# 白色角色当前制作检查点

更新：2026-10-03。当前白色静态候选已完成内部多角度检查，等待用户外观确认；这不是用户验收通过记录。进度 5/6。用户确认前，不进入紫色、橙色或绑定。

## 来源与工作入口

- 原始三件 GLB：`C:\Users\TimeCraker\Pictures\游戏人物建模参考\白色\3D模型`，未修改。
- 海报：`白色/海报参考图/01_主选海报参考图_厚底战术靴版.jpg`。
- 唯一制作源：`art/characters/white/rework/white_rework_working.blend`，纹理已打包。
- 运行资源：`client-godot-v2/models/characters/rework/white_static.glb`。
- 当前对象及可编辑控制说明：`art/characters/white/rework/README.md`。

## 本检查点保留的修复

原眉眼、头部基础网格及 UV 保持原样。右耳上缘原本穿过侧发，通过独立 `EarRim_ContactGuide` 和 12 个耳部顶点的选择组调整；未改眉眼区域。面部采用原贴图的柔和材质，减轻眼下和鼻梁的重阴影。刘海使用外层厚度控制笼，避免整件内推；长发侧部移至袖子后侧，重复耳周小物体用可恢复 MASK 去除，原主要发束保留。

袖子改为原生四边形网格与 Cloth 整理后的静态褶皱；模拟结果已冻结为网格，保留 Subdivision/Solidify。旧模拟源隐藏归档。身体前臂恢复连续表面，原服装的袖子/长手套筒用原生 Bisect 裁净，再连接袖口、肩带与垂带。原手套主体及贴合的腕扣保留，移除两侧远离手腕的悬空饰片。前襟使用原网格的干净布料材质，衣料厚度保留；长衣摆单独缩短至小腿位置。

生产集合 23 个网格，0 蒙皮，0 动作。保存源重新读取渲染与 Godot 实际载入一致。全部来源哈希及脸部几何/UV 检查见 `review/assembly_fit_20261002/structure_report.json`。

## 撤下的试验与恢复注意

大范围头皮投射造成裂面；焊接后丢失自定义法线、局部平滑发束造成破坏；新条带刘海轮廓过于简单并露出根部切口；耳周补片及光滑前襟长条未得到好的结果。均未采用到当前生产外观。

活动 Blender 曾退出，原因未确认；从保存的制作源重新启动成功。本轮最终使用的是保存源中的袖子与原衣片表面，前襟长条试验未保存到生产源。不要从 TEMP 试验脚本重新生成整个角色。

5 点 Lattice 的默认控制坐标是 -2 到 2；7 点轴是 -3 到 3。按真实坐标设置尺寸。后续继续在保存源上编辑，每个关键变化立即检查正/侧/背及头部图。

## 当前证据

`art/characters/white/rework/review/assembly_fit_comparison_20261002.png`、`assembly_head_comparison_20261002.png`、`assembly_fit_20261002/` 和 `godot_20261002/`。

旧 `source_detail_*`、旧 `godot/`、`checkpoint_*` 等为历史图。二维海报的光照、姿势和透视不能与正交休止模型机械匹配；没有用户外观确认，也没有帧时测量。

## 工具和复验命令

本机插件 socket 之前实测可用（127.0.0.1:9876），最后近景复核时活动进程已退出；此次采用 Blender 后台读取保存源、逐次渲染，桥接 `scripts/pipeline/characters/blender_live.py`；它与 Codex 原生 MCP 注册分别记录。启动 working blend 后插件自动连接已实测。

从 games 目录顺序执行，等待每条退出：

```powershell
& 'C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe' -b --python-exit-code 1 -P .\asternova\scripts\pipeline\characters\export_static_review.py -- --blend .\asternova\art\characters\white\rework\white_rework_working.blend --output .\asternova\client-godot-v2\models\characters\rework\white_static.glb
& 'C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe' -b --python-exit-code 1 -P .\asternova\scripts\pipeline\characters\render_static_review.py -- --blend .\asternova\art\characters\white\rework\white_rework_working.blend --output .\asternova\art\characters\white\rework\review\assembly_fit_20261002
& 'C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe' --headless --path .\asternova\client-godot-v2 --editor --import --quit
& 'C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe' --path .\asternova\client-godot-v2 --resolution 1280x900 res://scenes/character_lab/white_static_review.tscn -- --verify-white-static --evidence=C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/characters/white/rework/review/godot_20261002
```

不要最小化正在截图的 Godot，否则可能等待 `frame_post_draw`。导出和渲染不会保存或重建工作源。
