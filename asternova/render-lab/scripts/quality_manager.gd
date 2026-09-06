extends CanvasLayer

enum QualityTier { LOW, MEDIUM, HIGH }

@export var world_environment: WorldEnvironment
@export var cherry_particles: GPUParticles3D

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
	var tier_name: String = ""
	match current_tier:
		QualityTier.LOW: tier_name = "低档 (Low - 锁 60FPS / 关泛光)"
		QualityTier.MEDIUM: tier_name = "中档 (Medium - 120FPS / 标配)"
		QualityTier.HIGH: tier_name = "高档 (High - 解锁上限 / 全特效)"
	
	if fps_label:
		fps_label.text = "FPS: %d  |  当前画质: %s" % [fps, tier_name]
	if info_label:
		var method := RenderingServer.get_current_rendering_method()
		var method_name := "Forward+ (Vulkan Clustered)" if method == "forward_plus" \
				else method.to_upper()
		info_label.text = "渲染器: %s | 平台: Windows 64-bit\n快捷键: [1] 低档  [2] 中档  [3] 高档  | 鼠标拖拽: 360°环视  滚轮: 缩放" % method_name

func set_quality_tier(tier: QualityTier) -> void:
	current_tier = tier
	# 泛光/SSAO/SSR 参数一律以官方母版 endfield_studio_environment.tres 的法定值为准,
	# 三档切换只拨动开关与帧率/MSAA/粒子数, 严禁手改母版材质参数
	var env: Environment = world_environment.environment if world_environment else null
	match tier:
		QualityTier.LOW:
			Engine.max_fps = 60
			get_viewport().msaa_3d = Viewport.MSAA_DISABLED
			if env:
				env.glow_enabled = false
				env.ssao_enabled = false
				env.ssr_enabled = false
			if cherry_particles:
				cherry_particles.amount = 40
		QualityTier.MEDIUM:
			Engine.max_fps = 120
			get_viewport().msaa_3d = Viewport.MSAA_2X
			if env:
				env.glow_enabled = true
				env.ssao_enabled = true
				env.ssr_enabled = true
			if cherry_particles:
				cherry_particles.amount = 100
		QualityTier.HIGH:
			Engine.max_fps = 0 # 解锁至显示器上限
			get_viewport().msaa_3d = Viewport.MSAA_4X
			if env:
				env.glow_enabled = true
				env.ssao_enabled = true
				env.ssr_enabled = true
			if cherry_particles:
				cherry_particles.amount = 200
	_update_hud_label()

func _update_hud_label() -> void:
	var fps: float = Engine.get_frames_per_second()
	var tier_name: String = ""
	match current_tier:
		QualityTier.LOW: tier_name = "低档 (Low - 锁 60FPS / 关泛光)"
		QualityTier.MEDIUM: tier_name = "中档 (Medium - 120FPS / 标配)"
		QualityTier.HIGH: tier_name = "高档 (High - 解锁上限 / 全特效)"
	if fps_label:
		fps_label.text = "FPS: %d  |  当前画质: %s" % [fps, tier_name]
