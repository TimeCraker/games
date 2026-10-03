# 紫色后置兜帽与头颈修复：最新静态候选

2026-10-03。按用户反馈只调整紫色头颈区域；白色、橙色及旧资源未由本轮修改。用户未确认，绑定、变形和 Godot 验收尚未开始。

## 工程与来源

- 当前工程：`../../purple_source_repair.blend`，SHA-256 `037de42605efdb0bccfba259ee3a2701beaef3161df63765d66017acc977ab2b`。
- 当前 GLB：`../../exports/hood_back/purple_source_static_hood_back.glb`，SHA-256 `0dbc45d94f8440d08e4aeebc2f1698ded7f95d65e9bc04bcc1332ed388a12d7f`。
- 调整前戴帽工程：提交 `99450c6`，SHA-256 `6c629320eebe120e7968d573589de1cf7f2299e4314741b39e0f627f5de8996b`；原检查图、报告与静态 GLB 保留。
- 三件原 GLB 来源及哈希仍见 [source_manifest.json](../../source_manifest.json)，原件集合不编辑。

## 诊断与局部修复

当前工程实测为 0 骨架、0 动作。颈部显短发生在静态装配中；原素体头颈基础坐标未被缩短。原外领口组件最高点约 1.446 米，高于下巴约 1.413 米，遮挡了头颈轮廓。

通过 Blender MCP 短指令调用原生工具完成：

1. 原兜帽使用既有局部 Lattice 转至后颈并下垂，保留底部连接、原面、贴图与饰件。
2. 完整外领口及对应饰件原生整体降低 3.3 厘米，保留其形状与 UV；最高点降至约 1.413 米。
3. 头部使用独立颈根过渡 Lattice 整体抬高 1.5 厘米；长发和它的两件调整笼同步整体移动。原眉眼和脸形保持。
4. 兜帽放下后检查后脑，发现旧短发 Mask 会暴露内层空缺。停用这个可恢复 Mask，恢复原内层短发与头皮表面，长发作为外层覆盖。没有用新增球体或公式生成头皮。

每个区域修改后均立即取得 MCP 视口图并亲自检查；保存后重新渲染贴图、中性材质及正侧背头颈特写。

## 数据与导出核对

| 检查 | 实测结果 |
| --- | --- |
| 原服装面 | 47,502 个原面全部保留，原面编号无重复或缺失 |
| 原 UV | 服装逐原面、身体、头发均保持一致 |
| 身体完整性 | 求值后 53,433 个顶点，与源身体顶点数一致；短发 Mask 已停用 |
| 原脸形状 | 4,686 个保护顶点，扣除已记录的整体向上 1.5 厘米平移后，最大误差约 0.000000358 米 |
| 来源保护 | 渲染及导出前后工程哈希一致 |
| GLB | 8 件网格、4 个材质、3 张原贴图，所有图元含 UV 与法线，0 蒙皮、0 动作 |
| 重导入 | 正面、头部、背面与保存工程渲染一致，平均通道误差均小于 0.0011/255 |

测量见 [repair_report.json](repair_report.json)，渲染见 [purple_render_report.json](purple_render_report.json)，导出见 [purple_export_report.json](../../exports/hood_back/purple_export_report.json)，重导入见 [reimport_report.json](glb_reimport/reimport_report.json)。这些只验证数据保护和导出一致性，不代替用户美术确认或运行验收。

## 当前交付

- [兜帽与头颈前后同框](hood_neck_before_after.png)
- [完整正、左、右、背视图](purple_static_views.png)
- [中性材质四视图](purple_static_neutral.png)
- [参考、未修装配、旧失败方案与当前修复](purple_static_comparison.png)
- [完整头部、原侧脸与海报视角](purple_static_details.png)

15 张单视图包含完整穿戴的 `head`、`head_side`、`head_back`，以及临时隐藏外衣和独立长发的 `face_front`、`face_profile` 原脸检查图。原固定舞台配置不变，后颈特写相机另保存在工程的 `Purple_View_head_back`。图像、来源哈希及历史源提交见 [static_manifest.json](static_manifest.json)；图片只做等比缩放排版。

兜帽保留原网格折面，小饰件及边缘仍有原生成网格的棱面感。当前为静态微 A 姿态；权重、极限关节、衣摆和头发运动尚未测试。用户确认当前静态版本后，才从这个哈希建立 Rigify 副本并进入变形、九动作和 Godot 验证。

## 复现本版输出

PowerShell 命令仅读取保存工程，输出到本版独立目录：

```powershell
$taskBlender = 'C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe'
$taskProject = 'C:\Users\TimeCraker\Desktop\my_workspace\games\asternova'
$taskSource = "$taskProject\art\characters\purple\rework\source_repair"
$taskPipeline = "$taskProject\scripts\pipeline\characters\purple_rework.py"
& $taskBlender --factory-startup --background --python $taskPipeline -- --blend "$taskSource\purple_source_repair.blend" --output "$taskSource\review\hood_neck_fit" --mode render --review-profile "$taskSource\review\review_profile.json"
& $taskBlender --factory-startup --background --python $taskPipeline -- --blend "$taskSource\purple_source_repair.blend" --output "$taskSource\exports\hood_back" --mode export --filename purple_source_static_hood_back.glb
```
