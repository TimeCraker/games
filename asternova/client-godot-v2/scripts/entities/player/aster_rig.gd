class_name AsterRig
extends Node3D

## Aster 真身视觉骨架：NPR 着色实装 + 双插槽拔刀/纳刀 + AnimationTree 动捕驱动。
## 骨骼动作 100% 来自重定向动捕库（aster_animlib.res / aster_anim_tree.tres），
## 代码层零手搓骨骼姿态（红线：严禁 sin/cos、Tween 摆骨等程序化假动作）。

const SHADER_TOON := preload("res://shaders/toon_character.gdshader")
const SHADER_OUTLINE := preload("res://shaders/outline.gdshader")

# STYLE.md M1 定稿的二次元柔和冷紫阶梯调色
# 描边规范（任务书 Phase 4.3）：深灰青蓝 #3D435C，严禁纯黑；身体 0.0026 / 佩刀 0.0009
const OUTLINE_COLOR := Color8(0x3D, 0x43, 0x5C)
const OUTLINE_THICKNESS_BODY := 0.0026
const OUTLINE_THICKNESS_KATANA := 0.0009
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

var anim_player: AnimationPlayer = null
var anim_tree: AnimationTree = null
var katana_blade: MeshInstance3D = null
var hand_drawn_transform: Transform3D = Transform3D.IDENTITY
var is_drawn: bool = false
var blade_base_marker: Marker3D = null
var blade_tip_marker: Marker3D = null
var blade_trail: BladeRibbonTrail = null

# 单体局部卡肉序列号：连续冻结（如 3 段双刺两次卡肉）只由最后一次计时恢复
var _freeze_seq: int = 0

func _ready() -> void:
	_apply_npr(self)
	_locate_katana()
	_setup_blade_markers_and_trail()
	_setup_animation_system()
	# 玩家日常为纳刀态：入场即回鞘
	sheathe_sword(false)

# ==================== AnimationTree 动捕驱动 ====================

func _setup_animation_system() -> void:
	anim_player = AnimationPlayer.new()
	anim_player.name = "AnimationPlayer"
	anim_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
	$Aster_Armature.add_child(anim_player)  # root_node 默认 ".." → 轨道 "Skeleton3D:骨名" 直接解析
	anim_player.add_animation_library("", load("res://art/animations/aster_animlib.res"))

	# 先配置后入树：AnimationTree 的参数表在 READY 时按 tree_root 构建，
	# 入树后再设 tree_root 会错过构建（parameters/* 全部不存在）
	anim_tree = AnimationTree.new()
	anim_tree.name = "AnimationTree"
	anim_tree.anim_player = NodePath("../Aster_Armature/AnimationPlayer")
	anim_tree.tree_root = load("res://art/animations/aster_anim_tree.tres")
	anim_tree.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
	add_child(anim_tree)
	anim_tree.active = true
	# 状态机从 Start 节点不会自动进状态，需显式 start；deferred 保证 playback 参数已就绪
	call_deferred("_start_at", "Locomotion")

func _playback() -> AnimationNodeStateMachinePlayback:
	# SM 嵌在 BlendTree 根下，playback 路径 = parameters/SM/playback
	return anim_tree.get("parameters/SM/playback") as AnimationNodeStateMachinePlayback if anim_tree else null

func _start_at(state: String) -> void:
	var pb := _playback()
	if pb:
		pb.start(state)

func travel(state: String) -> void:
	var pb := _playback()
	if pb == null or pb.get_current_node() == StringName(state):
		return
	pb.travel(state)

func get_current_state_node() -> String:
	var pb := _playback()
	return String(pb.get_current_node()) if pb else ""

func set_locomotion_blend(speed: float) -> void:
	if anim_tree:
		anim_tree.set("parameters/SM/Locomotion/blend_position", speed)

## 单体局部卡肉：仅冻结自身 AnimationTree 播放速度（TimeScale=0），
## Engine.time_scale 恒为 1.0，UI/摄像机/环境满帧运转。
func freeze_pose(duration: float) -> void:
	if anim_tree == null:
		return
	_freeze_seq += 1
	var seq := _freeze_seq
	anim_tree.set("parameters/HitstopScale/scale", 0.0)
	get_tree().create_timer(duration).timeout.connect(func() -> void:
		if _freeze_seq == seq and anim_tree:
			anim_tree.set("parameters/HitstopScale/scale", 1.0)
	)

func get_clip_length(clip: String) -> float:
	if anim_player and anim_player.has_animation(clip):
		return anim_player.get_animation(clip).length
	return 0.4

# ==================== 刀光条带采样点 ====================

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
		outline.set_shader_parameter("outline_thickness",
				OUTLINE_THICKNESS_KATANA if mi.name.begins_with("Katana") else OUTLINE_THICKNESS_BODY)
		outline.set_shader_parameter("distance_scaling", true)
		mat.next_pass = outline
		mi.set_surface_override_material(i, mat)

func _locate_katana() -> void:
	katana_blade = hand_socket.get_node_or_null("Katana_Blade") as MeshInstance3D
	if katana_blade:
		hand_drawn_transform = katana_blade.transform
		# GLB 作者状态为右手握刀：初始记为拔刀态，交由 _ready 统一回鞘
		is_drawn = true

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
	clear_trail()
	blade_drawn_changed.emit(false)

func _mount_blade(new_parent: Node3D, local_transform: Transform3D) -> void:
	if katana_blade.get_parent() != null:
		katana_blade.get_parent().remove_child(katana_blade)
	new_parent.add_child(katana_blade)
	katana_blade.transform = local_transform

func get_katana_position() -> Vector3:
	return katana_blade.global_position if katana_blade else global_position + Vector3.UP
