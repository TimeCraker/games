# 白色角色返工工程：制作中，未通过美术验收

2026-10-01。制作源是 `white_rework_working.blend`，纹理已打包。`white_static_master.blend` 保留为用户否定的历史试验，禁止覆盖工作源。

## 本检查点

- 保留原素模五官：头部 1362 个 UV 角点与原身体全部对应，基础坐标差为 0。撤下眉眼镜像试验；原始左右眼设计保留。`Face_CleanForehead.002` 仅清理额头短发残留，保护深色眉眼和紫色虹膜。
- 完整长发分别用发冠、后发变形笼贴合头型。星形黑蓝银发夹替换旧枪刺状试验。
- 保留连续原手臂、原手套、独立腕带；Blender Cloth 制作静态袖褶，不代表运行时布料模拟。
- 衣摆改为尖角轮廓，蓝黑白三角块面和金色细线烘焙为可导出的贴图；腰部折片改为不对称尖角，圆裙片保留在隐藏归档。
- 蓝色翻领改为沿衣身垂下。腰带、扣件和衣片扣带单独可编辑；袖扣带使用 Shrinkwrap PROJECT / ON_SURFACE 贴合袖面，侧视确认撤下悬空条。
- 短裤改为独立双腿开口网格；腹部仅对源躯干岛使用可恢复腰部变形笼，不改脸、手臂或腿。

## 工具与制作源

活动 Blender 通过本机 Blender MCP 插件 socket 编辑，`blender_live.py` 是协议桥接，当前 Codex 没有原生 Blender MCP 工具。Windows Computer Use 已恢复并实际用于激活 Blender、切换正侧视、检查实时桌面视口；几何编辑、变形笼、投射和烘焙使用活动场景中的 Blender 原生能力。

`EXPORT_White` 包含当前可见工作对象。`SOURCE_ARCHIVE` 保留原部件；`REJECTED_ASSEMBLY` 保留撤下试验；`AUTHOR_ClothSimulation` 保留制作网格和变形笼。只读脸部比较对象与隐藏试验不参与导出。工作源可继续编辑，导出不按旧缩放参数重建。

## 查看与导出

从 games 根目录双击 `启动白色静态样板.bat`：1 新版、2 旧休止、3 旧 Idle；V 正侧背、H 头部、M 中性材质、P 转台、N Toon/PBR；右键环绕，滚轮缩放。

```powershell
& 'C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe' -b --python-exit-code 1 -P .\asternova\scripts\pipeline\characters\export_static_review.py -- --blend .\asternova\art\characters\white\rework\white_rework_working.blend --output .\asternova\client-godot-v2\models\characters\rework\white_static.glb
```

导出读取成品，不保存源；曲线临时转换成网格。`.export.json` 记录源和运行 GLB 哈希。Godot 重新导入退出后再运行展示，防止截图使用缓存版本。

## 证据与剩余差距

- `review/checkpoint_front.png`、`checkpoint_head.png`、`checkpoint_left.png`：本检查点 Blender 渲染。
- `review/godot/`：实际引擎正侧背、头部、中性材质、Toon/PBR 和旧版截图。
- `review/poster_old_current.png`：海报、旧动作原型、上一返工、本检查点同框。引擎版本相机和灯光一致；海报姿态、透视和布光不同。
- `review/checkpoint_structure.json`：源与导出哈希、隐藏对象排除及原始来源保留检查。
- `review/original_face_and_contact.json`：原五官对应关系、镜像试验未使用和袖扣带接触测量。
- `review/live_blender.png`、`wrist_hem.png` 是此前历史检查点，不代表本次结果。

主要差距仍是夹克的自然折叠和设计层次、肩颈与头发细节、皮肤和布料的精致呈现。腰折片目前保留明确可编辑结构，仍需美术打磨。Godot 使用原生 Toon/PBR 比较，尚未完成完整 NPR 和 SDF 面部。数据报告、截图和成功载入不能代替海报外观验收。

宏观进度仍为 2/6，白色未通过静态美术验收、未绑定。用户确认白色后才扩展紫色、橙色和绑定。
