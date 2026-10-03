# 紫色原资产修复工程

2026-10-03：按用户反馈将兜帽放至后颈、改善头颈显短，最新完整静态候选已交付，等待用户确认。当前工程 0 骨架、0 动作；Godot 运行尚未开始。

制作源：[purple_source_repair.blend](purple_source_repair.blend)，SHA-256 `037de42605efdb0bccfba259ee3a2701beaef3161df63765d66017acc977ab2b`。从三件原 GLB 重新导入，保留原件、眉眼、UV、贴图和独立工作副本。原来源与哈希见 [source_manifest.json](source_manifest.json)。本目录独立于上一轮紫色简化服装、绑定及运行实验。

集合：`SOURCE_Purple_Immutable` 原件；`WORK_Purple` 工作网格；`EDIT_Purple_Fit_Cages` 局部调整笼；`EXPORT_Purple` 导出；`REVIEW_Purple` 固定相机与灯光。原件保持隐藏，禁止编辑。模型通过紫色专用 MCP 的原生比例编辑、分件和局部变形笼修复，关键改动后立即截图检查。

原兜帽、长卷发、胸腰裁片、原袖子、腿环、垂饰及分层长衣摆保留；47,502 个原服装面和逐原面 UV 均保留。只补一枚实际断口的连接环。最新调整：外领口降低 3.3 厘米，头部与长发整体抬高 1.5 厘米，恢复原内层头发填补后脑空缺。详见 [最新静态交付报告](review/hood_neck_fit/static_review_report.md)。

- [兜帽与头颈前后对照](review/hood_neck_fit/hood_neck_before_after.png)
- [参考／原件装配／旧失败方案／新修复](review/hood_neck_fit/purple_static_comparison.png)
- [完整正、左、右、背视图](review/hood_neck_fit/purple_static_views.png)
- [中性材质四视图](review/hood_neck_fit/purple_static_neutral.png)
- [头部、原侧脸与海报视角](review/hood_neck_fit/purple_static_details.png)
- [15 张单视图和渲染记录](review/hood_neck_fit/)
- [交付图的来源及哈希](review/hood_neck_fit/static_manifest.json)
- [最新独立静态 GLB](exports/hood_back/purple_source_static_hood_back.glb) 与 [导出报告](exports/hood_back/purple_export_report.json)
- [最新 GLB 重导入及一致性检查](review/hood_neck_fit/glb_reimport/reimport_report.json)

侧脸隔离图临时隐藏衣服和独立长发，以检查原眉眼、鼻唇和耳侧；完整穿戴侧面及后颈另见 `review/hood_neck_fit/head_side.png`、`head_back.png`。海报视角使用静态微 A 姿态。小饰件仍有原网格棱面感，动作中的穿插和权重尚未检验。上一版戴帽工程保存在提交 `99450c6`，对应 `review/garment_fit/`、根目录旧交付板及 `exports/purple_source_static.glb`，均保留。

白色、橙色及共享计划保留协作边界；旧紫色工程、资源和实验文件保留。用户确认本工程哈希后，才从该版本建立 Rigify 副本并验证动作与 Godot。
