extends CanvasLayer

## AsterNova - M1 三档画质管家 (Forward+ / AgX 母版标定).
## 泛光/SSAO/SSR/体积雾的色彩定稿参数一律以官方母版
## endfield_studio_environment.tres 为准 (AgX 模式 4 / 曝光 1.0 / 太阳 1.1),
## 三档切换只拨动开关 + 帧率/MSAA/阴影分辨率/雾密度缩放/粒子数,
## 严禁在运行时回写母版材质参数 (.tres 文件本任务零改动)。
##
## | 档位 | 帧率 | MSAA | SSAO/SSR | 体积雾 | 方向阴影 | 花瓣 |
## | 低   | 60   | 关   | 关       | 关     | 1024     | 40   |
## | 中   | 120  | 2x   | 标准质量 | 弱 0.5x| 2048     | 100  |
## | 高   | 解锁 | 4x   | 全分辨率 | 高质量 | 4096     | 200  |

enum QualityTier { LOW, MEDIUM, HIGH }

@export var world_environment: WorldEnvironment
@export var cherry_particles: GPUParticles3D

## 母版体积雾密度只读快照 (中档 0.5x 弱雾, 高档原值)
var _master_fog_density := -1.0

@onready var info_label: Label = $MarginContainer/PanelContainer/MarginContainer/VBoxContainer/InfoLabel
@onready var fps_label: Label = $MarginContainer/PanelContainer/MarginContainer/VBoxContainer/FpsLabel
@onready var btn_low: Button = $MarginContainer/PanelContainer/MarginContainer/VBoxContainer/HBoxContainer/BtnLow
@onready var btn_med: Button = $MarginContainer/PanelContainer/MarginContainer/VBoxContainer/HBoxContainer/BtnMed
@onready var btn_high: Button = $MarginContainer/PanelContainer/MarginContainer/VBoxContainer/HBoxContainer/BtnHigh

var current_tier: QualityTier = QualityTier.HIGH


func _ready() -> void:
	btn_low.pressed.connect(func(): set_quality_tier(QualityTier.LOW))
	btn_med.pressed.connect(func(): set_quality_tier(QualityTier.MEDIUM))
	btn_high.pressed.connect(func(): set_quality_tier(QualityTier.HIGH))
	var env := _get_env()
	if env:
		_master_fog_density = env.volumetric_fog_density
	set_quality_tier(QualityTier.HIGH)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_1:
				set_quality_tier(QualityTier.LOW)
			KEY_2:
				set_quality_tier(QualityTier.MEDIUM)
			KEY_3:
				set_quality_tier(QualityTier.HIGH)

func _process(_delta: float) -> void:
	var fps: float = Engine.get_frames_per_second()
	if fps_label:
		fps_label.text = "FPS: %d  |  当前画质: %s" % [fps, _tier_name()]
	if info_label:
		var method := RenderingServer.get_current_rendering_method()
		var method_name := "Forward+ (Vulkan Clustered)" if method == "forward_plus" \
				else method.to_upper()
		info_label.text = "渲染器: %s | 平台: Windows 64-bit\n快捷键: [1] 低档  [2] 中档  [3] 高档  | 鼠标拖拽: 360°环视  滚轮: 缩放" % method_name

func _get_env() -> Environment:
	return world_environment.environment if world_environment else null


func _tier_name() -> String:
	match current_tier:
		QualityTier.LOW:
			return "低档 (Low - 锁60 / 阴影1024 / 关雾与后处理)"
		QualityTier.MEDIUM:
			return "中档 (Medium - 锁120 / 阴影2048 / 弱雾)"
		_:
			return "高档 (High - 解锁 / 阴影4096 / 高质量体积雾)"


func set_quality_tier(tier: QualityTier) -> void:
	current_tier = tier
	var env := _get_env()
	var vp := get_viewport()
	match tier:
		QualityTier.LOW:
			Engine.max_fps = 60
			vp.msaa_3d = Viewport.MSAA_DISABLED
			if env:
				env.glow_enabled = false
				env.ssao_enabled = false
				env.ssr_enabled = false
				env.volumetric_fog_enabled = false
			# 阴影分辨率: 方向光图集 1024, 全向光图集 2048
			RenderingServer.directional_shadow_atlas_set_size(1024, true)
			vp.positional_shadow_atlas_size = 2048
			if cherry_particles:
				cherry_particles.amount = 40
		QualityTier.MEDIUM:
			Engine.max_fps = 120
			vp.msaa_3d = Viewport.MSAA_2X
			if env:
				env.glow_enabled = true
				env.ssao_enabled = true
				env.ssr_enabled = true
				env.volumetric_fog_enabled = true
				env.volumetric_fog_density = _master_fog_density * 0.5
				# 弱雾: 时域重投影量调低 (更清透, 母版重投影开关保持不变)
				env.volumetric_fog_temporal_reprojection_amount = 0.85
			RenderingServer.directional_shadow_atlas_set_size(2048, true)
			vp.positional_shadow_atlas_size = 4096
			# SSAO 标准质量 + 全分辨率; SSR 半分辨率省带宽
			RenderingServer.environment_set_ssao_quality(
					RenderingServer.ENV_SSAO_QUALITY_MEDIUM, false, 0.0, 2, 0.5, 2.0)
			RenderingServer.environment_set_ssr_half_size(true)
			if cherry_particles:
				cherry_particles.amount = 100
		QualityTier.HIGH:
			Engine.max_fps = 0 # 解锁至显示器上限
			vp.msaa_3d = Viewport.MSAA_4X
			if env:
				env.glow_enabled = true
				env.ssao_enabled = true
				env.ssr_enabled = true
				env.volumetric_fog_enabled = true
				if _master_fog_density > 0.0:
					env.volumetric_fog_density = _master_fog_density
				# 高质量体积雾: 母版时域重投影全量累积
				env.volumetric_fog_temporal_reprojection_amount = 0.95
			RenderingServer.directional_shadow_atlas_set_size(4096, true)
			vp.positional_shadow_atlas_size = 4096
			# SSAO 高质量全分辨率 + SSR 全分辨率
			RenderingServer.environment_set_ssao_quality(
					RenderingServer.ENV_SSAO_QUALITY_HIGH, false, 0.0, 2, 0.5, 2.0)
			RenderingServer.environment_set_ssr_half_size(false)
			if cherry_particles:
				cherry_particles.amount = 200
	_update_hud_label()

func _update_hud_label() -> void:
	if fps_label:
		fps_label.text = "FPS: %d  |  当前画质: %s" % [
				Engine.get_frames_per_second(), _tier_name()]
