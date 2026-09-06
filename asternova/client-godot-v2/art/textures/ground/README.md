# Ground Pavement PBR 套件 (第四执行组 · Ground Pavement Pipeline)

> 生成器：`scripts/pipeline/environment/process_ground_pbr.py`（改动请重跑脚本，勿手改贴图）
> 输入底图：`art/references/ground/raw_*.png`（顶视概念漫反射）

## 资产清单与世界比例约定

| 贴图 | 尺寸 | 一张贴图覆盖的世界尺寸 | 备注 |
| :--- | :--- | :--- | :--- |
| `ground_tiles_albedo/normal/roughness/ao.png` | 2048² | **2.4m × 2.4m**（4×4 块 0.6m 防滑方砖） | normal 为 16-bit PNG，OpenGL +Y 上 |
| `ground_tactile_albedo/normal/roughness.png` | 2048² | **0.9m × 0.9m**（3×3 块 0.3m 盲道砖，每砖 4 条圆弧倒角凸条） | 处方：暖姜黄 #E5B23B，凸条 rough 0.50 / 底板 0.68 |
| `ground_asphalt_albedo/normal/roughness.png` | 2048² | **2.5m × 2.5m** | 四向无缝（镜像折叠），rough 0.82 基底 |
| `asphalt_clean_albedo.png` | 2048² | 同上 | Phase 1 无缝化中间产物（与 albedo 同图，语义命名） |
| `asphalt_white_stripe.png` (+ `_roughness`) | 512×2048 | **0.83m 宽 × 3.33m 长**，白实线位于 u∈[0.151, 0.46] | 仅纵向无缝；白漆 rough 0.58 / 沥青 0.82 |
| `ground_trim_sheet_2k.png` | 2048² | 集成条带图（仅 Albedo） | 象限布局见下 |

## Trim Sheet UV 分区（2048×2048, 像素坐标 [x0,y0]-[x1,y1]）

- 左上 TILES：[24, 24] - [1012, 1012]（uv 0.0117-0.4941 × 0.0117-0.4941）
- 右上 TACTILE：[1036, 24] - [2024, 1012]
- 左下 ASPHALT：[24, 1036] - [1012, 2024]
- 右下 WHITE-STRIPE TRIM：竖条居中 [1406, 1036] - [1653, 2024]

分隔带 24px，象限标注只画在留白带内。

## Godot 4.7 用法

着色器：`render-lab/shaders/toon_ground_pbr.gdshader`。GLB 地面网格顶面 UV 为退化
线性条，**必须启用 `use_world_uv = true`**，`world_uv_period = 上表世界尺寸(米)`
（vec2，各向异性可用），`uv_offset` 平移取样窗；`normal_depth` 调法线强度，
`sky_reflection_energy` 天光微泛光防死灰（≤0.2，远低于泛光阈值 1.6）。
坡道白实线用世界坐标驱动：`edge_stripe_line_width = 0.2`（米，0 关闭）、
`edge_stripe_center = 0`、`edge_stripe_half_width = 4.0`（路面半宽）、
`edge_stripe_u0 = 0.151`、`edge_stripe_span = 0.309`、
`edge_stripe_world_period = 3.33`、`edge_stripe_roughness = 0.58`。

实装方式：`ground_npr_setup.gd` 挂载于沙盒场景，对 GLB 现存地面网格
（Plaza_Sidewalk_West / Plaza_Tactile_Line / Plaza_Asphalt_Road /
Ramp_Asphalt_Road / Ramp_Sidewalk_West）运行时覆盖材质，严禁重建模。
场景：`render-lab/scenes/levels/modern_residential_sandbox.tscn` 与
`client-godot-v2/scenes/levels/modern_residential_sandbox.tscn`。
