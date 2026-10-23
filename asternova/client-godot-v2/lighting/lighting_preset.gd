@tool
class_name LightingPreset
extends Resource

## 一套完整的场景光照参数。保存为 .tres，挂到 LightingRig 上即生效。
## 参数含义与调整方法见 docs/lighting-guide.md。

@export var display_name: String = "未命名"

@export_group("太阳 Sun")
## 太阳离地平线的高度角：0 = 贴地（黄昏），90 = 正头顶（正午）
@export_range(-10.0, 90.0, 0.5) var sun_elevation: float = 40.0
## 太阳水平方位角：0 = 从 +Z 方向照来，90 = 从 +X 方向照来
@export_range(-180.0, 180.0, 0.5) var sun_azimuth: float = 135.0
@export var sun_color: Color = Color(1.0, 0.96, 0.90)
@export_range(0.0, 8.0, 0.01) var sun_energy: float = 1.0
## 太阳视角大小（度），越大影子边缘越软
@export_range(0.0, 5.0, 0.05) var sun_angular_size: float = 0.5
@export var sun_shadows: bool = true

@export_group("天空 Sky")
## 填了全景 HDRI 就用它当天空；留空则用下面的程序化天空颜色
@export var sky_panorama: Texture2D
@export_range(-180.0, 180.0, 1.0) var sky_rotation: float = 0.0
@export var sky_top_color: Color = Color(0.32, 0.48, 0.72)
@export var sky_horizon_color: Color = Color(0.72, 0.80, 0.88)
@export var ground_horizon_color: Color = Color(0.62, 0.64, 0.66)
@export var ground_bottom_color: Color = Color(0.20, 0.20, 0.22)
@export_range(0.0, 4.0, 0.01) var sky_energy: float = 1.0

@export_group("环境光 Ambient")
## 阴影里有多亮。整体太灰太平就降，阴影死黑就升
@export_range(0.0, 4.0, 0.01) var ambient_energy: float = 1.0
## 环境光有多少取自天空颜色（1 = 全部取天空，0 = 全部用下面的固定色）
@export_range(0.0, 1.0, 0.01) var ambient_sky_contribution: float = 1.0
@export var ambient_color: Color = Color(0.5, 0.55, 0.65)

@export_group("曝光与色彩 Exposure")
## 整体亮度。先调这个，再调太阳和环境光
@export_range(0.1, 4.0, 0.01) var exposure: float = 1.0
@export_range(0.5, 2.0, 0.01) var contrast: float = 1.0
@export_range(0.0, 2.0, 0.01) var saturation: float = 1.0

@export_group("全局光照 GI")
## SDFGI：实时光线反弹（墙面被照亮后会把颜色反射到地面和角色上）
@export var sdfgi_enabled: bool = true
@export_range(0.0, 4.0, 0.01) var sdfgi_energy: float = 1.0
@export_range(0.0, 1.5, 0.01) var sdfgi_bounce: float = 0.5
@export var ssil_enabled: bool = false
@export_range(0.0, 4.0, 0.01) var ssil_intensity: float = 1.0

@export_group("接触阴影与反射 AO / SSR")
@export var ssao_enabled: bool = true
@export_range(0.0, 8.0, 0.01) var ssao_intensity: float = 1.5
@export_range(0.1, 4.0, 0.01) var ssao_radius: float = 1.0
@export var ssr_enabled: bool = true

@export_group("雾 Fog")
## 距离雾：远处物体逐渐融入雾色，拉开空间纵深
@export var fog_enabled: bool = true
@export var fog_color: Color = Color(0.70, 0.78, 0.88)
@export_range(0.0, 0.05, 0.0001) var fog_density: float = 0.004
## 远景被天空颜色同化的程度（空气透视）
@export_range(0.0, 1.0, 0.01) var fog_aerial_perspective: float = 0.5
@export_range(0.0, 1.0, 0.01) var fog_sun_scatter: float = 0.1
## 体积雾：可以看见光柱，代价较高
@export var volumetric_fog_enabled: bool = false
@export_range(0.0, 0.2, 0.001) var volumetric_fog_density: float = 0.01
@export var volumetric_fog_albedo: Color = Color(0.8, 0.85, 0.9)

@export_group("辉光 Glow")
@export var glow_enabled: bool = true
@export_range(0.0, 4.0, 0.01) var glow_intensity: float = 0.4
## 多亮的像素开始发光。越低越多东西泛光
@export_range(0.0, 4.0, 0.01) var glow_threshold: float = 1.0
@export_range(0.0, 1.0, 0.01) var glow_bloom: float = 0.0

@export_group("场景人造光 Practical")
## 乘到场景里 "practical_light" 组的灯（招牌灯、店内灯、路灯）上。白天低、夜晚高
@export_range(0.0, 8.0, 0.01) var practical_light_scale: float = 1.0
