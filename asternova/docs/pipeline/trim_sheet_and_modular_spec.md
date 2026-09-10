# AsterNova 日系近未来建筑 Trim Sheet 贴图与模块化构件技术规范

> **文档版本**：v1.1（2026-09-10 适用范围收缩）  
> **制定者**：Master Architect (主脑)  
> **适用模块**：M1 街区视觉工业化重塑（对标 31 张权威参考图白皮书）  
> **对应着色器**：`res://shaders/toon_trim_pbr.gdshader`
>
> ⚠️ **适用范围收缩定案（2026-09-10 制作人拍板）**：本规范现仅适用于 **Tier 1 地面与道路基础设施**（第二节贴图条带 Band 0~7 与地面材质参考）。第三节「六大模块化建筑构件」**整节废弃**——建筑一律走 [modular_art_and_asset_production_sop.md](modular_art_and_asset_production_sop.md) 的「Tripo 底模 + 几何手术」管线，严禁再按本清单程序化拼装建筑立面。第四节着色器参数中的 toon 色阶（ramp_threshold / shadow_tint 等）**不适用于建筑硬表面**（场景纯 PBR 定案，见 STYLE.md §3），仅作地面材质存档参考。

---

## 一、 核心指导哲学：“2 渲染 3 的次世代清透写实”

本规范彻底终结“用纯立方体拉伸做建筑”的业余做法，引入 3A 工业级 **Trim Sheet（纹理装饰板）+ Modular Kit（模块化乐高构件）** 体系：
- **消灭 90° 刀片尖角**：所有结构边缘必须自带 **2~3cm 物理倒角（Bevel/Chamfer）**，在低角度日光下切出精细的高光轮廓线；
- **全场景复用 1 张 2K 贴图**：数百个建筑零件共用统一的 Trim Sheet，显存占用极低，千元手机端稳定 120 FPS；
- **PBR 微表面 + NPR 赛璐璐冷暖对撞**：受光面呈现金属与倒角 GGX 锐利高光，背阴面呈现清冷天光偏色，缝隙处 Cavity AO 自然加深，杜绝塑料漂浮感。

---

## 二、 Trim Sheet 贴图 8 大条带 UV 规范 (2048 × 2048)

贴图在垂直 V 方向均等划分为 8 个 256px 高度的横向条带（V 从 0.0 至 1.0），构件 UV 沿水平 U 轴无限平铺：

| 条带编号 | V 轴范围 (0~1) | 像素高度 | 材质类型 | 构件用途与微表面特性 | 典型参数 (Rough / Metal) |
| :---: | :---: | :---: | :---: | :--- | :---: |
| **Band 0** | `0.000 ~ 0.125` | 0~256px | 阳极氧化铝 | **屋顶防水压顶 (Parapet Cap) / 建筑收边倒角板**<br>双向倒角凹槽，受光侧切出锐利高光线 | Rough: 0.35<br>Metal: 0.85 |
| **Band 1** | `0.125 ~ 0.250` | 256~512px | 预制清水混凝土 | **外立面分缝面板 (Panel Seam) + 模板定位螺栓孔**<br>中央 4cm 深刻凹缝，微噪点肌理，无缝平铺 | Rough: 0.78<br>Metal: 0.00 |
| **Band 2** | `0.250 ~ 0.375` | 512~768px | 黄黑工业漆 | **45° 工业防撞警示条 (Hazard Stripes) / 转角护角**<br>工程黄 (#F5A623) 与碳黑强对撞，边缘微剥落 | Rough: 0.52<br>Metal: 0.05 |
| **Band 3** | `0.375 ~ 0.500` | 768~1024px | 涂层镀锌铁 | **通风百叶格栅 (Louver Grille) / 外机防护网**<br>斜切 45° 阴影法线，自带深层 AO 遮挡 | Rough: 0.45<br>Metal: 0.65 |
| **Band 4** | `0.500 ~ 0.625` | 1024~1280px | 冲压波纹钢板 | **商铺金属防盗卷闸门 (Roller Shutter)**<br>水平瓦楞波折，细腻法线起伏，商铺与变电房标配 | Rough: 0.40<br>Metal: 0.80 |
| **Band 5** | `0.625 ~ 0.750` | 1280~1536px | 粗凿花岗石 | **路沿石 (Curbstone) / 阶梯防滑踏步收口**<br>带 3cm 倒角磨损，表面微凹凸防滑槽 | Rough: 0.85<br>Metal: 0.00 |
| **Band 6** | `0.750 ~ 0.875` | 1536~1792px | 工业橡胶与套管 | **高空架空线缆束 (Cable Bundle) / 镀锌穿线管**<br>半光泽绝缘橡胶套管，带金属抱箍管卡 | Rough: 0.48<br>Metal: 0.30 |
| **Band 7** | `0.875 ~ 1.000` | 1792~2048px | 铸造生铁 | **下水雨水箅子 (Drain Grate) / 检修铸铁盖板**<br>经典网格镂空纹理，凹坑铸造颗粒感 | Rough: 0.65<br>Metal: 0.90 |

### 贴图通道标准：
1. `trim_modern_japan_2k_albedo.png` (sRGB, 2048x2048)
2. `trim_modern_japan_2k_normal.png` (OpenGL Tangent Normal, 16-bit 感觉平滑，2048x2048)
3. `trim_modern_japan_2k_orm.png` (R: Ambient Occlusion, G: Roughness, B: Metallic)
4. `trim_modern_japan_2k_emission.png` (RGB 发光通道，专用于信号指示灯与警示发光线)

---

## 三、 六大模块化建筑构件尺寸与倒角定义 (Modular Kit)

构件遵循严格的网格对齐标准（Grid Snapping: 1.0m / 0.5m / 0.1m），必须由 Blender bpy 脚本程序化生成：

### 1. `facade_wall_4x4_panel.glb`（标准立面预制分缝墙板）
- **尺寸**：宽 4.0m × 高 4.0m × 厚 0.3m
- **特征**：中央十字 4cm 深刻倒角凹槽，四周嵌入 4 枚定位圆螺栓；顶部自带 5cm 凸起挑檐线脚；
- **UV**：正反主面映射至 `Band 1`，倒角线脚映射至 `Band 0`。

### 2. `facade_louver_4x4.glb`（通风百叶建筑模块）
- **尺寸**：宽 4.0m × 高 4.0m × 厚 0.4m
- **特征**：下半部为清水混凝土墙基，上半部内凹 0.15m 并安装密集金属百叶排气窗；
- **UV**：百叶部分映射至 `Band 3`，边框映射至 `Band 0`，墙基映射至 `Band 1`。

### 3. `store_front_ground_4x4.glb`（一层商铺门头与卷帘门）
- **尺寸**：宽 4.0m × 高 4.0m × 厚 0.8m
- **特征**：带有 0.6m 挑出雨檐与招牌灯箱槽，下方为金属防盗卷闸门或落地大玻璃店门；
- **UV**：卷闸门映射至 `Band 4`，挑檐与包边映射至 `Band 0`，转角贴有 `Band 2` 黄黑防撞条。

### 4. `stairs_pedestrian_2x4.glb`（人行防滑步道石阶）
- **尺寸**：宽 2.0m × 纵深 4.0m × 阶梯总升程 1.5m（10 级台阶）
- **特征**：单级踏面宽 40cm、踢面高 15cm；踏面边缘自带 3cm 倒角磨损与防滑凹槽；
- **外挂**：右侧安装高 0.9m 的双横杆铸铁防撞安全护栏；
- **UV**：踏面映射至 `Band 5`，金属护栏映射至 `Band 0`。

### 5. `monorail_skybridge_segment.glb`（跨街轻轨钢桁架天桥）
- **尺寸**：跨度 16.0m × 宽 3.5m × 高 2.8m
- **特征**：粗犷工字钢桁架支撑，底座横跨街道上方空域（离地净空 6.5m）；桥体侧面贴有醒目的工程黄涂装与反光警示标识；
- **UV**：桁架钢梁映射至 `Band 0` 与 `Band 2`，检修走道映射至 `Band 7`。

### 6. `parapet_cap_corner_2m.glb`（屋顶铝合金防水压顶转角件）
- **尺寸**：长 2.0m × 宽 0.4m × 挑檐下垂 0.1m
- **特征**：建筑顶部防雨水滴落收边扣板，切出锐利高光；
- **UV**：映射至 `Band 0`。

---

## 四、 着色器绑定与参数定稿规范 (`toon_trim_pbr.gdshader`)

所有采用 Trim Sheet 的材质，在 Godot 中必须遵循如下参数基准：

```gdscript
# Material: res://materials/trim_modern_japan_mat.tres
shader = load("res://shaders/toon_trim_pbr.gdshader")
shader_parameter/albedo_color = Color(1.0, 1.0, 1.0, 1.0)
shader_parameter/normal_depth = 1.2
shader_parameter/roughness_scale = 1.0
shader_parameter/metallic_scale = 1.0
shader_parameter/ao_light_affect = 0.75

# 赛璐璐阶梯与冷暖对撞参数 (锁死)
shader_parameter/shadow_tint = Color(0.72, 0.78, 0.90, 1.0) # 清冷天光背阴偏色
shader_parameter/ramp_threshold = 0.45
shader_parameter/ramp_smoothness = 0.06
shader_parameter/shadow_strength = 0.50

# 倒角锐利高光 (Bevel Highlights)
shader_parameter/specular_power = 1.2
shader_parameter/specular_tint = Color(1.0, 0.97, 0.92, 1.0) # 暖金直接光高光
shader_parameter/bevel_specular_sharpness = 36.0
```

---

## 五、 子 Agent 分工执行流水线（落地指引）

主脑作为技术美术总监（Tech Art Director），将后续执行拆解为 **3 个互不阻塞、接口清晰的独立任务单元**：

### 任务 1：Blender 构件库程序化构建（可指派给建模子 Agent）
- **输入**：本规范第三节（尺寸与 UV 表）
- **动作**：运行无头 Python 脚本生成 6 件 `.glb` 资产并导出至 `art/models/modular_kit/`
- **验收标准**：尺寸绝对咬合、无非流形破面、边缘自带 2~3cm 倒角。

### 任务 2：跨街轻轨天桥与远景天际线装配（可指派给空间装配子 Agent）
- **输入**：`monorail_skybridge_segment.glb` 与天际线大厦轮廓
- **动作**：在斜坡上方 6.5m 净空横跨架桥，在远景封堵虚空灰雾
- **验收标准**：从玩家主视角看，天际线不再是空白灰雾，产生深邃的三层空间包裹感。

### 任务 3：低角度侧逆光与丁达尔光柱调校（可指派给布光渲染子 Agent）
- **输入**：太阳高度角 28°、方位角 135°、体积雾各向异性 0.82
- **动作**：调整 `DirectionalLight3D` 与 `WorldEnvironment`，使金色阳光穿过轻轨桥与电缆缝隙投射出清晰可见的金色光柱（God Rays）
- **验收标准**：2K 抓帧人眼审查，受光面暖、背光面冷、倒角高光清晰。

---
*AsterNova 核心资产规范，未经制作人核准禁止擅自篡改参数基准。*
