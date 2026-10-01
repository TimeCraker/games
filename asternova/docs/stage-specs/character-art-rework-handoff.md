# 三角色返工交接：先继续白色发型与头模贴合

更新：2026-10-01。交接前最新资产提交 `c58bab3`，工作区干净。本文是执行交接，不能作为美术验收结论。

## 1. 用户目标与当前边界

将白、紫、橙三个角色的身体、衣服、头发装配到接近各自主海报的外观，再绑定骨架并在 Godot 验证移动和动作。

**当前只推进白色静态样板。白色获得用户确认后，才能扩展紫橙及绑定。** 用户最近明确指出“发型和头模没有匹配上”，下一轮优先继续处理这处问题。

允许局部重做网格、拓扑、材质，原始 GLB 必须保留。技术方式自行选择，但关键修改后立即看真实图。不要用导出成功、距离下降、面数或骨数代替海报外观验收。

计划依据：`character-art-rework.md`。宏观进度仍 **2/6**；白色尚未完成静态美术验收。旧三角色动作原型不代表新版装配合格。

## 2. 环境和唯一制作源

- 工作区：`C:\Users\TimeCraker\Desktop\my_workspace\games`，PowerShell。
- 原始资产：`C:\Users\TimeCraker\Pictures\游戏人物建模参考`。
- 白色主参考：`白色\海报参考图\01_主选海报参考图_厚底战术靴版.jpg`。
- 白色原始模型：`白色\3D模型\01_素体_quad.glb`、`02_服装_quad.glb`、`03_头发_quad.glb`。
- **唯一当前制作源**：`asternova\art\characters\white\rework\white_rework_working.blend`。
- `white_static_master.blend` 是用户否定的历史试验，不能覆盖工作源。
- 当前运行资源：`asternova\client-godot-v2\models\characters\rework\white_static.glb`。
- 工程说明：`asternova\art\characters\white\rework\README.md`。

读取工作区及 `asternova/AGENTS.md`，其中 2026-10-01 返工校正优先于历史规则。不要重跑早期缩放、区间挪顶点或删面脚本重建角色；导出必须读取已经修好的 blend。

## 3. 已完成的实际修改

### 脸与身体

- 恢复原始连续手臂，分出原手套并对齐腕口；保留原身体来源。
- 分出脸部工作网格，处理后脑重复五官；原眉眼设计保留。
- **原眼睛不要再镜像矫正**：当前头部 1362/1362 UV 角点与原身体对应，基础顶点坐标差为 0。此前将原左右眼差异误判为故障，镜像试验已撤下。
- 当前脸材质 `Face_CleanForehead.002`，仅清额头短发残留。`Face_AlignedFeatures` 是被撤下的试验，不得重新用于生产导出。
- 腿部表面分离、平滑；短裤重建为双腿开口。腹部使用限定躯干岛的可恢复腰部变形笼。

### 头发——最近一轮

- 使用完整独立长发，工作对象 `Hair_Full_Work`，保留原始数据与早先发冠/后发变形笼。
- 新增 `HeadFit_CrownAndHairline_Cage` 和顶点组 `HeadFit_CrownAndHairline`，中央刘海、鬓角及后脑控制幅度独立。
- 收拢刘海前伸、发冠高度和后脑体积；刚性发夹随表面移位。
- 未选中的 31199 个顶点位移为 0，长发末端保留。
- 前刘海样本到头部的无符号最近距离中位数由约 6.3 cm 降至 3.3 cm。这只证明几何变化，不证明无穿插或已经好看。
- 修前对象 `Hair_BeforeHeadFit_20261001` 保留在隐藏归档。
- 更强的刘海尖端内推造成额头穿插和发束折弯，已撤下；不要启用 `REJECTED_BangTipClearance_Cage`。

### 服装与饰件

- 原生 Cloth 制作静态袖褶，保留可编辑工作网格；不代表运行时布料模拟。
- 夹克衣片、包边、拉链分别制作；蓝翻领改为沿衣身垂下。
- 衣摆改为尖角轮廓，蓝黑白三角图案、金细线烘焙到贴图。
- 重建不对称腰折片、腰带、扣件、星形黑蓝银发夹。
- 袖扣带此前仍悬空。修正 Shrinkwrap 的 OUTSIDE 误用，当前为 PROJECT / ON_SURFACE，已看正侧面和接触测量。

这些修改已有截图与提交，但角色整体仍有生硬、简化的观感。

## 4. 下一轮执行顺序

1. 打开当前 working blend，对照主海报和 `review/hair_fit_comparison.png`。先确认当前活动场景与磁盘制作源一致。
2. 单独隐藏头发观察原头模；再单独观察头发。检查前额发根、头顶分缝、鬓角、耳位、后脑内腔和侧面刘海前伸，不要再次把问题归为原眼睛不好。
3. 正面、左右侧面、背面、四分之三特写使用固定相机；同时检查贴图和中性材质。判断是根部贴合、发束设计还是源网格本身的问题。
4. 优先把发根和发冠真正适配头型。当前笼是可编辑起点，不要求保留其造型。若再两轮调整仍无明显改善，复制派生工作网格，将刘海/侧发/后发按实际结构分开，局部重建发根、发束或拓扑；不要继续叠加整片空间修正。
5. 保留眼睛露出、脸部轮廓和蓝色挑染。避免整件头发统一缩小、用刘海遮住脸，或为了避穿插把所有长发移到错误位置。检查耳周碎片、交叠和重复饰件。
6. 发型贴合改善后，再继续夹克自然折叠、腰折片层次、肩颈/腕口接缝和材质呈现。当前服装仍偏像简单硬片，不能仅添扣件就算完成。
7. 保存 working blend，导出 GLB，等待 Godot 重新导入退出后再运行截图。更新多视图、同框比较和已知问题，独立提交。
8. 白色静态候选完成后交给用户确认。此前不做紫橙，不绑定。

每一步都以实际图像决定是否保留修改。眼睛、服装等非当前问题不要顺手重做。

## 5. Blender 工程组织与工具状态

- `EXPORT_White`：当前生产对象，导出 34 个网格，当前 **0 蒙皮、0 动作**。
- `SOURCE_ARCHIVE`：原始部件。
- `REJECTED_ASSEMBLY`：撤下试验。
- `AUTHOR_ClothSimulation`：制作网格与变形笼。
- `READONLY_FaceComparison`：只读脸部诊断对象。
- 隐藏归档、制作笼及诊断对象不能导出。

上一轮实测 Blender MCP 插件 socket `127.0.0.1:9876` 可以读取/编辑活动场景。桥接脚本 `asternova/scripts/pipeline/characters/blender_live.py`；**这不等于 Codex 注册了原生 Blender MCP 工具**。新 agent 需重新验证。

Windows Computer Use 已恢复，实际取得 Blender 桌面截图并切换视图。需要时读取 computer-use 技能，以 `@oai/sky` 从返回窗口重新选择 Blender；不复用旧截图坐标或窗口状态。插件截图可能是按相机离屏渲染，真正桌面视口用 Computer Use 检查。任何方式都不能保证美术质量。

Blender：`C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe`。

Godot：`C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe`。

## 6. 导出与引擎检查

以下从 games 根目录执行，按顺序等待完成：

```powershell
& 'C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe' -b --python-exit-code 1 -P .\asternova\scripts\pipeline\characters\export_static_review.py -- --blend .\asternova\art\characters\white\rework\white_rework_working.blend --output .\asternova\client-godot-v2\models\characters\rework\white_static.glb

& 'C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe' --headless --path .\asternova\client-godot-v2 --editor --import --quit

& 'C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe' --path .\asternova\client-godot-v2 --resolution 1280x900 res://scenes/character_lab/white_static_review.tscn -- --verify-white-static --evidence=C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/characters/white/rework/review/godot
```

导出器读取成品，不保存/覆盖制作源。GLB 旁 `.export.json` 记录源与导出哈希；更新后检查与截图一致。

双击根目录 `启动白色静态样板.bat` 查看。1 新版、2 旧休止、3 旧 Idle；V 正侧背、H 头部、M 中性材质、P 转台、N Toon/PBR；右键环绕、滚轮缩放。

当前 Godot 使用 Forward+ / AgX，原生 Toon/PBR 比较；面部平光观察源贴图。完整 NPR、SDF 面部尚未完成，不宣称最终渲染品质或 120 FPS。

## 7. 证据与提交

证据根目录：`asternova/art/characters/white/rework/review/`。

- `hair_fit_comparison.png`：本次头发修前/修后正侧面对照及海报头部。
- `hair_fit_front/side/threequarter/back.png`：局部头部检查。
- `hair_fit_measurements.json`：局部变形及未选区域保持记录。
- `checkpoint_front/head/left.png`：最新 Blender 渲染。
- `godot/`：最新实际引擎多视图。
- `poster_old_current.png`：海报及版本间全身对照。
- `checkpoint_structure.json`：源/导出哈希一致、来源未改、归档排除；`art_approved=false`。
- `original_face_and_contact.json`：原五官对应、镜像试验撤下、袖带接触。
- `live_blender.png`、`wrist_hem.png` 是旧检查点，不代表本次结果。

最近提交：

- `c58bab3`：发型与头模分区贴合。
- `61c1f65`：保留原五官、修服装贴合、衣摆及饰件。
- `612ebfc`：Computer Use 恢复验证记录。

临时诊断脚本曾放 OS temp，不能当作长期制作入口。下一 agent 应以保存的 blend 和已提交导出器接续。

## 8. 白色静态验收门槛

脸部神态和身体比例接近海报方向；头发贴合头型，眼睛露出合理；肩腰腿轮廓清楚；衣服正确穿在身体上，袖口与手臂连贯；正侧背和转台没有明显悬空、穿插、缺面或漂浮碎片。

交付全身多视图、头部特写、海报/旧版对照、可编辑工程和 Godot 展示。**自动报告证明数据，真实图像证明表现，最终静态外观由用户确认。**

确认后才按总计划完成紫橙，再以 Rigify 制作控制骨架、制作蒙皮和辅助骨链、验证极限姿态、重定向现有有许可的九段动作并完成 Godot 移动/动作检查。
