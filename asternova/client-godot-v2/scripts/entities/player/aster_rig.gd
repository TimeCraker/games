class_name AsterRig
extends Node3D

## Aster 真身视觉骨架：NPR 着色实装 + 双插槽拔刀/纳刀 + 程序化握点挥刀
## （纯节点与代码层控制，不产生任何粒子特效）

const SHADER_TOON := preload("res://shaders/toon_character.gdshader")
const SHADER_OUTLINE := preload("res://shaders/outline.gdshader")

# STYLE.md M1 定稿的二次元柔和冷紫阶梯调色
const OUTLINE_COLOR := Color(0.24, 0.26, 0.36, 1.0)
const OUTLINE_THICKNESS := 0.0022
const SHADOW_TINT := Color(0.82, 0.84, 0.92, 1.0)
const RAMP_THRESHOLD := 0.48
const RAMP_SMOOTHNESS := 0.04
const RIM_COLOR := Color(0.85, 0.92, 1.0, 1.0)
const KATANA_ATLAS_FALLBACK := "res://models/aster/katana_basecolor.png"

## 纳刀位姿（刀身相对左腰鞘插槽的局部变换，工程标定用）
@export var sheathe_transform: Transform3D = Transform3D.IDENTITY

## 刀身采样标记偏移（Katana_Blade 网格空间：原点≈护手，-Y 为实际刀尖延伸端）
@export var blade_base_offset: Vector3 = Vector3.ZERO
@export var blade_tip_offset: Vector3 = Vector3(0.0, -0.7, 0.0)

signal blade_drawn_changed(is_drawn: bool)

@onready var skeleton: Skeleton3D = $Aster_Armature/Skeleton3D
@onready var hand_socket: BoneAttachment3D = $Aster_Armature/Skeleton3D/Hand_R_Weapon_Socket
@onready var scabbard_socket: BoneAttachment3D = $Aster_Armature/Skeleton3D/Pelvis_L_Scabbard_Socket

var katana_blade: MeshInstance3D = null
var hand_drawn_transform: Transform3D = Transform3D.IDENTITY
var is_drawn: bool = false
var blade_base_marker: Marker3D = null
var blade_tip_marker: Marker3D = null
var blade_trail: BladeRibbonTrail = null

# 程序化挥刀：以右手腕握点为轴心的骨骼姿态偏移（欧拉角，度）
const SOCKET_BONE := "Hand_R_Weapon_Socket"
const UPPERARM_BONE := "R_Upperarm"
const SWING_REST := Vector3.ZERO

# 各段挥击的关键帧姿态：windup(前举起手) -> strike(挥出) -> 回位
const SWING_POSES := {
	0: [Vector3(35, 0, -55), Vector3(-55, 0, 65)],    # 1段挑击：右下斜撩而上
	1: [Vector3(-20, -75, -25), Vector3(-30, 80, 25)], # 2段反削：左进右出平削
	2: [Vector3(-10, 0, 10), Vector3(95, 0, 0)],      # 3段双连刺：刀尖指前突刺
	3: [Vector3(95, -30, 0), Vector3(95, 40, 0)],     # 4段回旋：刀身横展周身回旋
}
const IAI_POSE := [Vector3(20, 100, 0), Vector3(-15, -115, 0)] # 居合拔刀横斩
const GUARD_POSE := Vector3(15, 40, 45)                        # 纳刀架刀：刀贴腰际

# 手臂挥动关键帧：肩→手期望方向（骨架空间，-Z 前方 / +X 右侧 / +Y 上）
const SWING_ARM_DIRS := {
	0: [Vector3(0.7, -0.5, 0.3), Vector3(0.15, 0.55, -0.82)],  # 1段挑击：右手低后位撩至前上
	1: [Vector3(0.6, 0.0, -0.8), Vector3(0.65, 0.1, -0.75)], # 2段反削：手臂稳持前举，身体横扫出弧
	2: [Vector3(0.5, -0.25, 0.2), Vector3(0.05, 0.05, -1.0)],  # 3段双连刺：收手回拉直刺前方
	3: [Vector3(0.95, -0.1, -0.2), Vector3(0.95, 0.15, -0.35)], # 4段回旋：手臂平展右侧随体旋转
}
const IAI_ARM_DIRS := [Vector3(-0.45, -0.35, 0.0), Vector3(0.7, 0.0, -0.6)] # 居合：左手收刀位横斩至右前
const GUARD_ARM_DIR := Vector3(-0.35, -0.45, -0.15)                         # 架刀：手探左腰握柄

var _socket_rest_quat: Quaternion = Quaternion.IDENTITY
var _socket_bone_idx: int = -1
var _upperarm_idx: int = -1
var _upperarm_parent_idx: int = -1
var _upperarm_rest_quat: Quaternion = Quaternion.IDENTITY
var _rest_arm_dir: Vector3 = Vector3(0.79, -0.62, 0.0)
var _swing_tween: Tween = null
var _freeze_tween: Tween = null
var _body_sweep_tween: Tween = null

## 单体局部卡肉：命中瞬间冻结骨骼位姿（暂停挥刀姿态动画），倒计时后恢复
func freeze_pose(duration: float) -> void:
	if _swing_tween and _swing_tween.is_valid():
		_swing_tween.pause()
	if _freeze_tween and _freeze_tween.is_valid():
		_freeze_tween.kill()
	_freeze_tween = create_tween()
	_freeze_tween.tween_interval(duration)
	_freeze_tween.tween_callback(_unfreeze_pose)

func _unfreeze_pose() -> void:
	if _swing_tween and _swing_tween.is_valid():
		_swing_tween.play()

func _ready() -> void:
	_apply_npr(self)
	_locate_katana()
	_setup_blade_markers_and_trail()
	_capture_socket_rest()
	# 玩家日常为纳刀态：入场即回鞘
	sheathe_sword(false)

func _setup_blade_markers_and_trail() -> void:
	if katana_blade == null:
		return
	blade_base_marker = Marker3D.new()
	blade_base_marker.name = "Blade_Base"
	blade_base_marker.position = blade_base_offset
	katana_blade.add_child(blade_base_marker)
	blade_tip_marker = Marker3D.new()
	blade_tip_marker.name = "Blade_Tip"
	blade_tip_marker.position = blade_tip_offset
	katana_blade.add_child(blade_tip_marker)
	blade_trail = BladeRibbonTrail.new()
	blade_trail.name = "BladeRibbonTrail"
	add_child(blade_trail)
	blade_trail.setup(blade_base_marker, blade_tip_marker, skeleton)

func set_trail_active(active: bool) -> void:
	if blade_trail:
		blade_trail.set_active(active)

func clear_trail() -> void:
	if blade_trail:
		blade_trail.clear_trail()

func get_blade_base_position() -> Vector3:
	return blade_base_marker.global_position if blade_base_marker else get_katana_position()

func get_blade_tip_position() -> Vector3:
	return blade_tip_marker.global_position if blade_tip_marker else get_katana_position()

func _locate_katana() -> void:
	katana_blade = hand_socket.get_node_or_null("Katana_Blade") as MeshInstance3D
	if katana_blade:
		hand_drawn_transform = katana_blade.transform
		# GLB 作者状态为右手握刀：初始记为拔刀态，交由 _ready 统一回鞘
		is_drawn = true

func _capture_socket_rest() -> void:
	_socket_bone_idx = skeleton.find_bone(SOCKET_BONE)
	if _socket_bone_idx >= 0:
		_socket_rest_quat = skeleton.get_bone_rest(_socket_bone_idx).basis.get_rotation_quaternion()
	_upperarm_idx = skeleton.find_bone(UPPERARM_BONE)
	if _upperarm_idx >= 0:
		_upperarm_parent_idx = skeleton.get_bone_parent(_upperarm_idx)
		_upperarm_rest_quat = skeleton.get_bone_rest(_upperarm_idx).basis.get_rotation_quaternion()
		var cur_global := skeleton.get_bone_global_pose(_upperarm_idx).basis.get_rotation_quaternion()
		_rest_arm_dir = (cur_global * Vector3.UP).normalized() # 骨骼 +Y 指向肘部

# ==================== NPR 着色实装 ====================

func _apply_npr(root: Node) -> void:
	for child in root.get_children():
		if child is MeshInstance3D:
			_setup_mesh(child)
		_apply_npr(child)

func _setup_mesh(mi: MeshInstance3D) -> void:
	for i in mi.mesh.get_surface_count():
		var src := mi.get_active_material(i)
		var albedo_tex: Texture2D = null
		if src is BaseMaterial3D:
			albedo_tex = src.albedo_texture
		elif src is ShaderMaterial:
			albedo_tex = src.get_shader_parameter("albedo_texture")
		# Godot 可能在部分刀身表面丢失共享图集 -> 黑面渲染兜底
		if albedo_tex == null and mi.name.begins_with("Katana"):
			albedo_tex = load(KATANA_ATLAS_FALLBACK)
		var mat := ShaderMaterial.new()
		mat.render_priority = 0
		mat.shader = SHADER_TOON
		mat.set_shader_parameter("albedo_color", Color(1, 1, 1, 1))
		mat.set_shader_parameter("albedo_texture", albedo_tex)
		mat.set_shader_parameter("desaturation", 0.0)
		mat.set_shader_parameter("use_alpha_scissor", false)
		mat.set_shader_parameter("shadow_tint", SHADOW_TINT)
		mat.set_shader_parameter("ramp_threshold", RAMP_THRESHOLD)
		mat.set_shader_parameter("ramp_smoothness", RAMP_SMOOTHNESS)
		mat.set_shader_parameter("shadow_strength", 0.45)
		mat.set_shader_parameter("enable_rim", true)
		mat.set_shader_parameter("rim_color", RIM_COLOR)
		mat.set_shader_parameter("rim_threshold", 0.65)
		mat.set_shader_parameter("rim_smoothness", 0.04)
		mat.set_shader_parameter("rim_spread", 2.2)
		mat.set_shader_parameter("specular_color", Color(0.95, 0.97, 1.0, 1.0))
		mat.set_shader_parameter("specular_size", 0.05)
		mat.set_shader_parameter("specular_smoothness", 0.015)
		var outline := ShaderMaterial.new()
		outline.render_priority = 1
		outline.shader = SHADER_OUTLINE
		outline.set_shader_parameter("outline_color", OUTLINE_COLOR)
		outline.set_shader_parameter("outline_thickness", OUTLINE_THICKNESS)
		outline.set_shader_parameter("distance_scaling", true)
		mat.next_pass = outline
		mi.set_surface_override_material(i, mat)

# ==================== 拔刀 / 纳刀 插槽切换 ====================

func draw_sword(instant: bool = true) -> void:
	if is_drawn or katana_blade == null:
		return
	is_drawn = true
	_mount_blade(hand_socket, hand_drawn_transform if instant else hand_drawn_transform)
	blade_drawn_changed.emit(true)

func sheathe_sword(instant: bool = true) -> void:
	if not is_drawn or katana_blade == null:
		return
	is_drawn = false
	_mount_blade(scabbard_socket, sheathe_transform)
	_reset_swing_pose()
	blade_drawn_changed.emit(false)

func _mount_blade(new_parent: Node3D, local_transform: Transform3D) -> void:
	if katana_blade.get_parent() != null:
		katana_blade.get_parent().remove_child(katana_blade)
	new_parent.add_child(katana_blade)
	katana_blade.transform = local_transform

func get_katana_position() -> Vector3:
	return katana_blade.global_position if katana_blade else global_position + Vector3.UP

# ==================== 程序化挥刀姿态（纯骨骼代码动画） ====================

func play_swing(stage: int) -> void:
	if _socket_bone_idx < 0:
		return
	var keyframes: Array = SWING_POSES.get(stage, SWING_POSES[0])
	var arm_dirs: Array = SWING_ARM_DIRS.get(stage, SWING_ARM_DIRS[0])
	_start_swing_timeline(keyframes[0], keyframes[1], arm_dirs[0], arm_dirs[1])
	# 2段反削：身体刚体横扫（左转蓄势右转挥出），刀尖划出宽阔水平弧线
	if stage == 1:
		_start_body_sweep(-28.0, 42.0)

func _start_body_sweep(from_deg: float, to_deg: float) -> void:
	_kill_body_sweep_tween()
	_body_sweep_tween = create_tween()
	_body_sweep_tween.tween_property(self, "rotation:y", deg_to_rad(from_deg), 0.05)
	_body_sweep_tween.tween_property(self, "rotation:y", deg_to_rad(to_deg), 0.12)
	_body_sweep_tween.tween_property(self, "rotation:y", 0.0, 0.18)

func _kill_body_sweep_tween() -> void:
	if _body_sweep_tween and _body_sweep_tween.is_valid():
		_body_sweep_tween.kill()
		_body_sweep_tween = null
	rotation.y = 0.0

func play_iaijutsu_swing() -> void:
	if _socket_bone_idx < 0:
		return
	_start_swing_timeline(IAI_POSE[0], IAI_POSE[1], IAI_ARM_DIRS[0], IAI_ARM_DIRS[1])

func play_guard_pose() -> void:
	if _socket_bone_idx < 0:
		return
	_kill_swing_tween()
	_swing_tween = create_tween()
	_swing_tween.tween_method(_apply_swing_euler, SWING_REST, GUARD_POSE, 0.12)
	_swing_tween.parallel().tween_method(_apply_arm_dir, _rest_arm_dir, GUARD_ARM_DIR, 0.12)

func _start_swing_timeline(windup_pose: Vector3, strike_pose: Vector3, windup_dir: Vector3, strike_dir: Vector3) -> void:
	_kill_swing_tween()
	set_trail_active(true)
	_swing_tween = create_tween()
	# 前举蓄势 0.05s -> 挥出 0.12s -> 平滑回位 0.18s
	_swing_tween.tween_method(_apply_swing_euler, SWING_REST, windup_pose, 0.05)
	_swing_tween.parallel().tween_method(_apply_arm_dir, _rest_arm_dir, windup_dir, 0.05)
	_swing_tween.tween_method(_apply_swing_euler, windup_pose, strike_pose, 0.12)
	_swing_tween.parallel().tween_method(_apply_arm_dir, windup_dir, strike_dir, 0.12)
	_swing_tween.tween_method(_apply_swing_euler, strike_pose, SWING_REST, 0.18)
	_swing_tween.parallel().tween_method(_apply_arm_dir, strike_dir, _rest_arm_dir, 0.18)
	# 挥刀结束停止采样，尾迹随后自然淡出
	_swing_tween.tween_callback(set_trail_active.bind(false))

func _reset_swing_pose() -> void:
	_kill_swing_tween()
	_kill_body_sweep_tween()
	_apply_swing_euler(SWING_REST)
	if _upperarm_idx >= 0:
		skeleton.set_bone_pose_rotation(_upperarm_idx, _upperarm_rest_quat)
	set_trail_active(false)
	clear_trail()

func _kill_swing_tween() -> void:
	if _swing_tween and _swing_tween.is_valid():
		_swing_tween.kill()
		_swing_tween = null

func _apply_swing_euler(euler_deg: Vector3) -> void:
	if _socket_bone_idx < 0:
		return
	var offset_quat := Quaternion.from_euler(Vector3(deg_to_rad(euler_deg.x), deg_to_rad(euler_deg.y), deg_to_rad(euler_deg.z)))
	skeleton.set_bone_pose_rotation(_socket_bone_idx, _socket_rest_quat * offset_quat)

func _apply_arm_dir(dir: Vector3) -> void:
	## 将肩→手方向平滑转向 dir：对 R_Upperarm 骨骼全局姿态施加最短弧旋转
	## （直接在全局空间求旋转，避免依赖骨骼局部轴向标定）
	if _upperarm_idx < 0 or dir.length_squared() < 0.001:
		return
	var target := dir.normalized()
	var cur_global := skeleton.get_bone_global_pose(_upperarm_idx).basis.get_rotation_quaternion()
	var cur_dir := cur_global * Vector3.UP
	var axis := cur_dir.cross(target)
	if axis.length_squared() < 1e-8:
		return
	var delta := Quaternion(axis.normalized(), cur_dir.angle_to(target))
	var target_global := delta * cur_global
	var parent_global := skeleton.get_bone_global_pose(_upperarm_parent_idx).basis.get_rotation_quaternion()
	skeleton.set_bone_pose_rotation(_upperarm_idx, parent_global.inverse() * target_global)
