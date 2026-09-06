# Ground Pavement PBR 套件 2.1 (第四执行组 · Ground Pavement Pipeline)

> 生成器：`scripts/pipeline/environment/process_ground_pbr.py`（改动请重跑脚本，勿手改贴图）
> 2.1 = 程序化分频平铺 + 真实骨料颗粒（主脑纠偏令落地版）。

## 资产清单与世界比例约定

| 贴图 | 尺寸 | 世界尺寸 | 处方 |
| :--- | :--- | :--- | :--- |
| `ground_tiles_albedo/normal/roughness/ao.png` | 2048² | **2.4m × 2.4m**（4×4 块 0.6m 方砖） | 白场 #D5D8DC~#E0E0E8（STYLE 标定），勾缝 #3E3B36 + 2~3px 曲率微倒角；砖面 rough 0.65 / 缝 0.88 |
| `ground_tactile_albedo/normal/roughness.png` | 2048² | **0.9m × 0.9m**（3×3 块 0.3m，每砖 4 根圆弧胶囊凸条） | 暖姜黄 #CFA132~#E5B23B；凸条 rough 0.48 / 底板 0.68 |
| `ground_asphalt_albedo/normal/roughness.png` | 2048² | **2.5m × 2.5m** | 深灰冷调 **#34373D**，骨料颗粒明度 0.18~0.26 自然波动（禁双边磨皮）；rough 0.82 / 压实暗带 0.60；法线带骨料咬合；四向无缝 2×2 梯度比 < 1.30 |
| `road_marking_edge_decal.png` (+ `_roughness`) | 512×2048 RGBA | **0.2m 宽 × 0.8m 长** 纵向无缝 | 白漆 #E8ECF0，2px 亚像素倒角；rough 0.55 |
| `manhole_cover_decal.png` (+ `_normal/_roughness/_metallic`) | 1024² RGBA | 0.97m 正圆井盖 | 铸铁 #34373D，16 螺栓孔 / 齿纹雨水凹槽 / 星形水道局徽章；rough 0.42 / metallic 0.45 |

## Godot 4.7 用法（Forward+ / ACES）

着色器 `toon_ground_pbr.gdshader`：`use_world_uv = true` + `world_uv_period` =
上表世界尺寸。**无 EMISSION 伪天光**（纠偏令）：天光反射由 roughness +
ReflectionProbe(box_projection) 自然呈现；`ambient_fill` 为自定义 light() 的
环境漫射补偿（沥青 1.4 / 方砖盲道 0.35）。
关键参数：沥青 `normal_depth 0.9` + `diffuse_gain 0.85`（砖/盲道 0.14 / 0.5，
白场调和解）；白实线 `edge_stripe_line_width 0.2`、`roughness 0.55`、
纵向周期 0.8m，世界 x 驱动 => 坡道到广场全程连贯；斑马线 `crosswalk_center_z 13.5`
纵深 2.6m、0.45m 白条（世界 z 驱动，坡道底部）。
井盖：`Cylinder_086/.087` 无盖空心管运行时加盖贴花圆盘（GLB z 镜像后世界 (-2.2,+18)）；
悬空红环装饰按节点名隐藏（Mirror/Ring/Torus + Cylinder_16/17/18/19/2 前缀）。
像素红线验收：`scripts/pipeline/environment/check_ground_review_pixels.py`。
