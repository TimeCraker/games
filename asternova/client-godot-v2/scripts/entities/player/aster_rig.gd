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

# ==================== §3 零偏置可拔刀架构常量 ====================
# weapon-modeling-pipeline.md §3：刀身/刀鞘建模原点锁定刀鞘口 Koiguchi (0,0,0)，
# 刀刃沿建模 -Z 延伸 0.70m，刀柄延伸至 +0.25m，握心（右手扣合点）在建模 +Z 0.13m。
# GLB Y-up 导出轴向映射：Blender +Z → Godot +Y（握心 = 网格空间 +Y 0.13），
# Blender +Z 0.13 握心补偿 → Godot 插槽空间 (0, -0.13, 0)。
const GRIP_CENTER_LOCAL := Vector3(0.0, 0.13, 0.0)          # 握心（刀身网格空间）
const DRAW_GRIP_COMPENSATION := Vector3(0.0, -0.13, 0.0)    # 拔刀握心回拉（插槽骨空间）

## 纳刀位姿（刀身相对左腰鞘插槽的局部变换；_ready 时以刀鞘 authored 变换标定，
## 即两分件网格空间完全重合的严丝合缝态）
@export var sheathe_transform: Transform3D = Transform3D.IDENTITY

## 刀身采样标记偏移（Katana_Blade 网格空间：原点≈护手，-Y 为实际刀尖延伸端）
@export var blade_base_offset: Vector3 = Vector3.ZERO
@export var blade_tip_offset: Vector3 = Vector3(0.0, -0.7, 0.0)

signal blade_drawn_changed(is_drawn: bool)

@onready var skeleton: Skeleton3D = (get_node_or_null("Aster_Armature/Skeleton3D") as Skeleton3D) if has_node("Aster_Armature/Skeleton3D") else ((get_node_or_null("Rig/Skeleton3D") as Skeleton3D) if has_node("Rig/Skeleton3D") else find_child("Skeleton3D", true, false) as Skeleton3D)
@onready var hand_socket: BoneAttachment3D = skeleton.get_node_or_null("Hand_R_Weapon_Socket") as BoneAttachment3D if skeleton else null
@onready var scabbard_socket: BoneAttachment3D = skeleton.get_node_or_null("Pelvis_L_Scabbard_Socket") as BoneAttachment3D if skeleton else null

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

## 循环剪辑表（glTF 不携带循环标记，导入后逐剪辑打 LOOP_LINEAR）
const LOOP_CLIPS := ["idle", "LightIdle", "LightWalking", "LightRunning", "Sprint",
	"crouch-run", "fall", "fall-landing", "wall-slide-front", "Guarding"]

func _setup_animation_system() -> void:
	# 首选 GLB 内嵌烘焙动画库（Blender 离线烘焙产物，场景根下自带 AnimationPlayer）
	anim_player = get_node_or_null("AnimationPlayer") as AnimationPlayer
	if anim_player == null:
		anim_player = find_child("AnimationPlayer", true, false) as AnimationPlayer
	if anim_player != null:
		anim_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
		var lib := anim_player.get_animation_library("")
		
		# 桥接别名映射表：将 Rigify 原生动捕剪辑映射给 FSM / AnimationTree
		var aliases := {
			"idle": "Idle", "LightIdle": "Idle", "LightWalking": "Walk",
			"LightRunning": "Jog_Fwd", "jump": "Jump", "fall": "Jump",
			"fall-landing": "Jump_Land", "Slash1": "Sword_Attack",
			"Slash2": "Sword_Attack", "Slash3": "Sword_Attack",
			"SlashUppercut": "Sword_Attack", "SlashCharge": "Sword_Idle",
			"SlashRelease": "Sword_Attack", "Guarding": "Sword_Idle",
			"GuardParry": "Sword_Idle", "wall-slide-front": "Jump",
			"HeavyJumpAttack": "Sword_Attack", "Hurt1": "Hit_Chest",
			"crouch-run": "Crouch_Fwd"
		}
		for alias_name in aliases:
			var src: String = aliases[alias_name]
			if lib.has_animation(src) and not lib.has_animation(alias_name):
				lib.add_animation(alias_name, lib.get_animation(src))
				
		for clip in LOOP_CLIPS:
			if lib.has_animation(clip):
				lib.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
	else:
		# 兜底：旧 Godot 重定向库（aster_animlib.res）
		anim_player = AnimationPlayer.new()
		anim_player.name = "AnimationPlayer"
		anim_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
		var arm: Node = get_node_or_null("Aster_Armature") if has_node("Aster_Armature") else get_node_or_null("Rig")
		if arm:
			arm.add_child(anim_player)
		else:
			add_child(anim_player)
		anim_player.add_animation_library("", load("res://art/animations/aster_animlib.res"))

	# 先配置后入树：AnimationTree 的参数表在 READY 时按 tree_root 构建，
	# 入树后再设 tree_root 会错过构建（parameters/* 全部不存在）
	anim_tree = AnimationTree.new()
	anim_tree.name = "AnimationTree"
	# 内嵌播放器在本节点直下（"../AnimationPlayer"）；兜底播放器在臂架下（"../Aster_Armature/AnimationPlayer"）
	var player_siblings_root := anim_player.get_parent() == self
	anim_tree.anim_player = NodePath("../AnimationPlayer") if player_siblings_root \
			else NodePath("../Aster_Armature/AnimationPlayer")
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
		# §3 拔刀挂载 = authored 握持滚转基（掌心对齐）+ 握心回拉补偿：
		# 使刀柄握心（网格 +Y 0.13）精确落点右手掌心（插槽骨原点），绝不脱手悬空
		hand_drawn_transform = Transform3D(Basis.IDENTITY, DRAW_GRIP_COMPENSATION)
		is_drawn = true
	# 纳刀标定：刀鞘分件的 authored 变换 = 两分件网格空间重合（Koiguchi 对齐入鞘）
	var scab := scabbard_socket.get_node_or_null("Katana_Scabbard") as MeshInstance3D
	if scab:
		sheathe_transform = scab.transform

## 刀柄握心世界坐标（拔刀态 = 右手掌心；物理抓握断言用）
func get_grip_center_world() -> Vector3:
	if katana_blade == null:
		return global_position + Vector3.UP
	return katana_blade.global_transform * GRIP_CENTER_LOCAL

## 右手掌心世界坐标（Socket 骨即标定于掌心处；与拔刀握心精确重合）
func get_palm_center_world() -> Vector3:
	if hand_socket:
		return hand_socket.global_position
	var skel := skeleton
	if skel == null:
		return global_position + Vector3.UP
	var idx := skel.find_bone("R_Hand")
	if idx == -1:
		idx = skel.find_bone("DEF-hand.R")
	if idx == -1:
		return global_position + Vector3.UP
	var pose := skel.global_transform * skel.get_bone_global_pose(idx)
	return pose * Vector3(0.0, 0.0812, 0.0)

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
