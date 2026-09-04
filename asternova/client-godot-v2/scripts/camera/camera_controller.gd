class_name CameraController
extends Node3D

## 双视角（第三人称越肩 + 第一人称主观）与动态爽感运镜系统

enum CameraMode {
	TPP, ## 第三人称越肩跟随
	FPP  ## 第一人称主观视角
}

@export var combat_data: CombatData
@export var mouse_sensitivity: float = 0.0025
@export var min_pitch: float = -75.0
@export var max_pitch: float = 75.0

@onready var spring_arm: SpringArm3D = $SpringArm3D
@onready var camera: Camera3D = $SpringArm3D/Camera3D

var current_mode: CameraMode = CameraMode.TPP
var current_pitch: float = 0.0
var current_yaw: float = 0.0

# 震屏能量 (Trauma 0.0 ~ 1.0)
var trauma: float = 0.0
var trauma_time: float = 0.0

# 顿帧计时器
var hitstop_timer: float = 0.0

# 内部过渡目标
var target_arm_length: float = 2.8
var target_arm_offset: Vector3 = Vector3(0.45, 1.35, 0.0)
var current_arm_offset: Vector3 = Vector3(0.45, 1.35, 0.0)

signal view_mode_changed(is_first_person: bool)

func _ready() -> void:
	if not combat_data:
		combat_data = CombatData.new()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	target_arm_length = combat_data.camera_tpp_distance
	target_arm_offset = combat_data.camera_tpp_offset
	current_arm_offset = target_arm_offset
	spring_arm.spring_length = target_arm_length
	spring_arm.position = current_arm_offset

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		var motion: Vector2 = event.relative * mouse_sensitivity
		current_yaw -= motion.x
		current_pitch = clampf(current_pitch - motion.y, deg_to_rad(min_pitch), deg_to_rad(max_pitch))
		
		# 旋转根节点水平水平偏航 (Yaw)
		rotation.y = current_yaw
		spring_arm.rotation.x = current_pitch

	if event.is_action_pressed("toggle_view"):
		toggle_camera_mode()

	if event.is_action_pressed("ui_cancel"):
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		else:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func toggle_camera_mode() -> void:
	if current_mode == CameraMode.TPP:
		current_mode = CameraMode.FPP
		target_arm_length = 0.0
		target_arm_offset = combat_data.camera_fpp_offset
		view_mode_changed.emit(true)
	else:
		current_mode = CameraMode.TPP
		target_arm_length = combat_data.camera_tpp_distance
		target_arm_offset = combat_data.camera_tpp_offset
		view_mode_changed.emit(false)

func _process(delta: float) -> void:
	# 1. 模式插值过渡
	spring_arm.spring_length = lerpf(spring_arm.spring_length, target_arm_length, delta * 12.0)
	current_arm_offset = current_arm_offset.lerp(target_arm_offset, delta * 12.0)
	spring_arm.position = current_arm_offset

	# 2. 震屏结算 (Trauma Shake 平方衰减)
	if trauma > 0.0:
		trauma = maxf(0.0, trauma - delta * combat_data.trauma_decay)
		trauma_time += delta * 45.0
		var shake_amount: float = trauma * trauma # 平方衰减手感更扎实
		var offset_x: float = sin(trauma_time * 1.2) * 0.15 * shake_amount
		var offset_y: float = cos(trauma_time * 1.5) * 0.15 * shake_amount
		var roll: float = sin(trauma_time) * 0.05 * shake_amount
		camera.h_offset = offset_x
		camera.v_offset = offset_y
		camera.rotation.z = roll
	else:
		camera.h_offset = lerpf(camera.h_offset, 0.0, delta * 15.0)
		camera.v_offset = lerpf(camera.v_offset, 0.0, delta * 15.0)
		camera.rotation.z = lerpf(camera.rotation.z, 0.0, delta * 15.0)

## 由角色控制器在 _physics_process 中通知当前速度与状态，用于动态拉伸 FOV 与贴地俯冲
func update_speed_feel(speed: float, is_sliding: bool, delta: float) -> void:
	# 动态广角 FOV
	var speed_ratio: float = clampf((speed - combat_data.walk_speed) / (combat_data.slide_initial_speed - combat_data.walk_speed), 0.0, 1.0)
	var target_fov: float = lerpf(combat_data.fov_base, combat_data.fov_max, speed_ratio)
	camera.fov = lerpf(camera.fov, target_fov, delta * 8.0)

	# 滑铲贴地俯冲感
	if current_mode == CameraMode.TPP:
		if is_sliding:
			target_arm_offset.y = combat_data.slide_height
		else:
			target_arm_offset.y = combat_data.camera_tpp_offset.y

## 触发打击卡肉顿帧与震屏
func trigger_hit_impact(is_heavy: bool = false) -> void:
	var hitstop_dur: float = combat_data.hitstop_heavy if is_heavy else combat_data.hitstop_light
	var shake_power: float = 0.75 if is_heavy else 0.35
	add_trauma(shake_power)
	
	# 触发微顿帧 (局部时间缩放，忽略 time_scale 的真实计时恢复)
	Engine.time_scale = 0.05
	get_tree().create_timer(hitstop_dur, true, false, true).timeout.connect(
		func(): Engine.time_scale = 1.0
	)

func add_trauma(amount: float) -> void:
	trauma = clampf(trauma + amount, 0.0, 1.0)

func get_aim_ray() -> Dictionary:
	var space_state: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	var screen_center: Vector2 = get_viewport().get_visible_rect().size / 2.0
	var from: Vector3 = camera.project_ray_origin(screen_center)
	var to: Vector3 = from + camera.project_ray_normal(screen_center) * 100.0
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(from, to)
	query.collision_mask = 1 | 2 # 检测环境与实体
	return space_state.intersect_ray(query)

func get_aim_direction() -> Vector3:
	var screen_center: Vector2 = get_viewport().get_visible_rect().size / 2.0
	return camera.project_ray_normal(screen_center)
