# 紫色原资产修复：完整静态候选交付

日期：2026-10-03。紫色专用 Blender MCP；Blender 5.2.1 LTS。

当前状态：静态制作和交付图已完成；用户确认待定；绑定、变形、九动作和 Godot 验收未开始。进度为本轮 5/8，不继承旧紫色工程的完成或验收记录。

## 工程及版本

| 项目 | 文件 | SHA-256 |
| --- | --- | --- |
| 当前候选工程 | `../purple_source_repair.blend` | `6c629320eebe120e7968d573589de1cf7f2299e4314741b39e0f627f5de8996b` |
| 静态 GLB | `../exports/purple_source_static.glb` | `2a6e83e74d2dc3d8d1395dbd685dcce4041dc556616be6860684a1af84128b22` |
| 初始原件装配 | 从本轮初始提交只读提取至临时目录，渲染见 `comparison/original_assembly/` | `3747fbb7f6c4d021bafd490aa0c3c9c021e1f9ace21f1745eb5d1dd90336c830` |
| 旧失败方案 | `../../purple_rework_working.blend`，渲染见 `comparison/old_failed/` | `3d6ab86ae89d78091b23a3c4895773ff9aec35862a5beceee005eb1c8b42fea4` |

原素体、服装、头发来源、哈希和只读约定见 [source_manifest.json](../source_manifest.json)。三件原 GLB 均无骨架和动作；实际网格为三角面，文件名中的 `quad` 不作为拓扑结论。三张原 8K 图像保留并打包。

## 实际修复

- 按头、肩、领口和胸腰关系装配原网格；服装前移问题在工作副本中纠正。原件集合不编辑。
- 保留原脸、眉眼、肤色、手套和高跟靴。重复的素体短发采用可恢复 Mask，保护额头、耳侧和原脸。
- 主长卷发使用左右独立局部 Lattice 后移，保留前侧卷束；刘海使用原生比例编辑抬高；原兜帽局部调整，为发冠留出空间。
- 原胸前裁片和内衣分别以受顶点组限制的 Lattice 适配，减少重叠。身体双臂以独立局部 Lattice 适配原袖子的微 A 姿态，腕部单独对齐袖口。原袖子与饰件保留。
- 原腿环及垂饰用原生分件保留 UV，再分别调整大小和位置。左侧原垂饰有 16.9 毫米连接断口，补一枚原生圆环连接件；其余裁片、纹样和饰件均来自原网格。
- 衣摆保留原白、黑、紫裁片、折线、边饰及层次。没有全局合并、填洞或重网格化。
- 曾尝试移动原袖子，但两轮检查发现衣摆或肩袖碎片受牵连，已撤回该方法；改为调整素体双臂与袖口局部。未持续叠加失败变形。
- 背面及中性材质的灰色噪点经灯光隔离确认来自补光和轮廓光的阴影；固定检查配置关闭这两盏灯的阴影，主光阴影保留，三种模型对照共用相同配置。

模型形状调整使用 Blender 原生短操作。Python 负责 MCP 调用胶水、测量、渲染、导出和对照图排版，没有用顶点公式生成替代服装。

## 检查及证据

| 检查 | 实测结果 | 记录 |
| --- | --- | --- |
| 原服装面与 UV | 47,502 个原面全部保留，原面编号无重复或缺失，逐原面 UV 一致 | `garment_fit/garment_fit_report.json` |
| 身体与头发 UV | 与原件一致 | 同上 |
| 原脸保护 | 4,686 个受保护顶点全部存在，求值后最大位置误差约 0.000000121 米 | 同上 |
| 固定舞台 | 正、左、右、背、头部、侧头部、四分之三和海报视角；锁定尺度、灯光、背景 | `review_profile.json` |
| 完整图像 | 14 张单视图，另有 4 张交付板；已亲自查看贴图及中性材质四视图 | `garment_fit/`、`static_manifest.json` |
| 原件及旧方案对照 | 相同检查配置、相同画面尺度 | `comparison/` |
| 导出只读 | 保存工程导出前后哈希一致 | `../exports/purple_export_report.json` |
| GLB 结构 | 8 件网格、4 个材质、3 张原贴图；0 蒙皮、0 动作；所有图元含 UV 和法线 | `glb_reimport/reimport_report.json` |
| GLB 图像一致性 | 正面、头部、背面重导入渲染与保存工程渲染相比，平均通道误差均小于 0.0011/255 | 同上 |

GLB 图像一致性只检查导出保真。原脸坐标与 UV 测量只检查数据保护，均不能替代用户的美术确认。

## 交付图

- [参考／未修原件装配／旧失败方案／新修复同框](purple_static_comparison.png)
- [完整正、左、右、背视图](purple_static_views.png)
- [中性材质四视图](purple_static_neutral.png)
- [头部、原侧脸与海报视角](purple_static_details.png)

14 张单视图：`front`、`left`、`right`、`back`、`head`、`head_side`、`threequarter`、`poster`、`clay`、`clay_left`、`clay_right`、`clay_back`、`face_front`、`face_profile`。全部位于 `garment_fit/`。`static_manifest.json` 记录各图、各板的哈希及来源工程或参考；排版只做等比缩放，不修饰模型图像。

## 已知限制及确认项

小金属饰件、细带及部分边缘仍具有原生成网格的棱面感；原拓扑的 UV/法线接缝和正常薄片边界保留。当前固定视图未见此前的整体错位、前臂穿袖和腿环悬空问题，不能据此保证所有任意视角、动作或极限姿态都无穿插。

兜帽在纯侧面遮住较多脸部，因此补充 `face_front`、`face_profile` 隔离图：临时隐藏服装及独立长发，恢复原短发，检查原眉眼、鼻唇和耳侧；它们不是完整穿戴效果。完整兜帽侧面见 `head_side`。海报视角保持静态微 A 姿态，海报的动作、布料动态和插画光效尚未制作。

静态验收由用户确认本工程版本；确认后记录哈希、建立绑定副本，再进行 Rigify、分区权重、主发束及衣摆辅助骨链、极限姿态、九动作和 Godot 实际画面。当前没有建立或导出这些内容，也没有改变任何旧 Godot 资源引用。

## 复现导出与检查图

在 PowerShell 中使用已安装的 Blender；所有命令仅读取制作源。

```powershell
$taskBlender = 'C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe'
$taskProject = 'C:\Users\TimeCraker\Desktop\my_workspace\games\asternova'
$taskSource = "$taskProject\art\characters\purple\rework\source_repair"
$taskPipeline = "$taskProject\scripts\pipeline\characters\purple_rework.py"
& $taskBlender --factory-startup --background --python $taskPipeline -- --blend "$taskSource\purple_source_repair.blend" --output "$taskSource\review\garment_fit" --mode render --review-profile "$taskSource\review\review_profile.json"
& $taskBlender --factory-startup --background --python $taskPipeline -- --blend "$taskSource\purple_source_repair.blend" --output "$taskSource\exports" --mode export --filename purple_source_static.glb
```

本轮只提交独立 `source_repair` 产物、紫色 Stage Spec 和紫色读取/导出入口；白色、橙色、共享计划及历史紫色实验保留。
