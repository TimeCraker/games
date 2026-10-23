class_name CharacterRig
extends Node3D

## 玩家视觉骨架：当前挂 CC0 中性人偶（models/mannequin，Quaternius Universal Animation Library），
## 正式角色按 docs/pipeline/character-pipeline.md 做好后替换模型即可，本脚本不绑定具体角色。
## 职责：AnimationTree 动画驱动 + 双插槽拔刀/纳刀 + 刀光采样点。
## 骨骼动作 100% 来自动画库，代码层不手搓骨骼姿态。

const SHADER_TOON := preload("res://shaders/toon_character.gdshader")
const SHADER_OUTLINE := preload("res://shaders/outline.gdshader")
const KATANA_SCENE := preload("res://models/weapons/katana.glb")
const ANIM_TREE_PATH := "res://art/animations/player_anim_tree.tres"

const OUTLINE_COLOR := Color8(0x3D, 0x43, 0x5C)
const OUTLINE_THICKNESS_KATANA := 0.0009

# 刀身/刀鞘网格原点 = 刀鞘口 (Koiguchi)，刀刃沿网格 -Y 延伸 0.70m，握心在网格 +Y 0.13m。
const GRIP_CENTER_LOCAL := Vector3(0.0, 0.13, 0.0)
const DRAW_GRIP_COMPENSATION := Vector3(0.0, -0.13, 0.0)

@export_group("插槽 (Sockets)")
## 右手握刀骨与左腰挂鞘骨（人偶为 Rigify 命名）
@export var hand_bone: StringName = &"DEF-hand.R"
@export var scabbard_bone: StringName = &"DEF-hips"
## 握心在手骨空间的位置与朝向（刀柄 = 局部 +Y）；换角色或刀不对齐时在这里调
@export var hand_grip_position: Vector3 = Vector3(0.0, 0.08, 0.02)
@export var hand_grip_rotation_deg: Vector3 = Vector3(-90.0, 0.0, 0.0)
## 鞘口在骨架空间（角色朝 +Z、左侧 +X、单位米）的位置，与刀柄指向
@export var scabbard_position: Vector3 = Vector3(0.17, 0.95, 0.10)
@export var scabbard_handle_direction: Vector3 = Vector3(-0.15, 0.35, 1.0)

@export_group("刀光")
## 刀身采样标记偏移（Katana_Blade 网格空间：-Y 为刀尖延伸端）
@export var blade_base_offset: Vector3 = Vector3.ZERO
@export var blade_tip_offset: Vector3 = Vector3(0.0, -0.7, 0.0)

signal blade_drawn_changed(is_drawn: bool)

var skeleton: Skeleton3D = null
var hand_socket: Node3D = null
var scabbard_socket: Node3D = null
var anim_player: AnimationPlayer = null
var anim_tree: AnimationTree = null
var katana_blade: MeshInstance3D = null
var katana_scabbard: MeshInstance3D = null
var sheathe_transform: Transform3D = Transform3D.IDENTITY
var hand_drawn_transform: Transform3D = Transform3D(Basis.IDENTITY, DRAW_GRIP_COMPENSATION)
var is_drawn: bool = false
var blade_base_marker: Marker3D = null
var blade_tip_marker: Marker3D = null
var blade_trail: BladeRibbonTrail = null

# 单体局部卡肉序列号：连续冻结（如 3 段双刺两次卡肉）只由最后一次计时恢复
var _freeze_seq: int = 0

func _ready() -> void:
	skeleton = find_child("Skeleton3D", true, false) as Skeleton3D
	_setup_sockets()
	_setup_katana()
	_setup_blade_markers_and_trail()
	_setup_animation_system()
	# 玩家日常为纳刀态
	sheathe_sword(false)

# ==================== AnimationTree 动画驱动 ====================

## 状态树沿用的剪辑名 → 人偶动画库剪辑名。换动画库时只改这张表。
const CLIP_ALIASES := {
	"idle": "Idle_Loop", "LightIdle": "Idle_Loop", "LightWalking": "Walk_Loop",
	"LightRunning": "Jog_Fwd_Loop", "Sprint": "Sprint_Loop",
	"jump": "Jump_Start", "fall": "Jump_Loop", "fall-landing": "Jump_Land",
	"wall-slide-front": "Jump_Loop", "crouch-run": "Crouch_Fwd_Loop",
	"Slash1": "Sword_Attack", "Slash2": "Sword_Attack", "Slash3": "Sword_Attack",
	"SlashUppercut": "Sword_Attack", "SlashRelease": "Sword_Attack",
	"HeavyJumpAttack": "Sword_Attack", "SlashCharge": "Sword_Idle",
	"Guarding": "Sword_Idle", "GuardParry": "Sword_Idle", "Hurt1": "Hit_Chest",
}

## 循环剪辑表（按别名）
const LOOP_CLIPS := ["idle", "LightIdle", "LightWalking", "LightRunning", "Sprint",
	"crouch-run", "fall", "fall-landing", "wall-slide-front", "Guarding"]

func _setup_animation_system() -> void:
	anim_player = find_child("AnimationPlayer", true, false) as AnimationPlayer
	if anim_player == null:
		push_warning("CharacterRig: 模型里没有 AnimationPlayer，动画不可用")
		return
	anim_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
	var lib := anim_player.get_animation_library("")
	for alias_name in CLIP_ALIASES:
		if lib.has_animation(alias_name):
			continue
		var src := _resolve_clip(lib, CLIP_ALIASES[alias_name])
		if src != "":
			lib.add_animation(alias_name, lib.get_animation(src))
		else:
			push_warning("CharacterRig: 动画库缺少剪辑 %s（别名 %s）" % [CLIP_ALIASES[alias_name], alias_name])
	for clip in LOOP_CLIPS:
		if lib.has_animation(clip):
			lib.get_animation(clip).loop_mode = Animation.LOOP_LINEAR

	# 先配置后入树：AnimationTree 的参数表在 READY 时按 tree_root 构建，
	# 入树后再设 tree_root 会错过构建（parameters/* 全部不存在）
	anim_tree = AnimationTree.new()
	anim_tree.name = "AnimationTree"
	anim_tree.tree_root = load(ANIM_TREE_PATH)
	anim_tree.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
	anim_player.get_parent().add_child(anim_tree)
	anim_tree.anim_player = anim_tree.get_path_to(anim_player)
	anim_tree.active = true
	# 状态机从 Start 节点不会自动进状态，需显式 start；deferred 保证 playback 参数已就绪
	call_deferred("_start_at", "Locomotion")

## Godot 导入时可能保留或去掉 _Loop 后缀，两种都认
func _resolve_clip(lib: AnimationLibrary, clip: String) -> String:
	for candidate in [clip, clip.trim_suffix("_Loop"), clip + "_Loop"]:
		if lib.has_animation(candidate):
			return candidate
	return ""

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

# ==================== 插槽与佩刀 ====================

## 插槽 = BoneAttachment3D（跟骨）下的一个偏移节点。
## 鞘口偏移按骨架空间书写，再换算到骨骼局部，便于直观调参。
func _setup_sockets() -> void:
	if skeleton == null:
		push_warning("CharacterRig: 未找到 Skeleton3D")
		return
	var hand_offset := Transform3D(Basis.from_euler(hand_grip_rotation_deg * (PI / 180.0)), hand_grip_position)
	hand_socket = _make_socket(hand_bone, "Hand_R_Weapon_Socket", hand_offset, false)

	var y := scabbard_handle_direction.normalized()
	var x := (Vector3.RIGHT - y * Vector3.RIGHT.dot(y)).normalized()
	var scabbard_skeleton_space := Transform3D(Basis(x, y, x.cross(y)), scabbard_position)
	scabbard_socket = _make_socket(scabbard_bone, "Pelvis_L_Scabbard_Socket", scabbard_skeleton_space, true)

func _make_socket(bone: StringName, socket_name: String, offset: Transform3D, offset_in_skeleton_space: bool) -> Node3D:
	var idx := skeleton.find_bone(bone)
	if idx == -1:
		push_warning("CharacterRig: 骨架缺少骨骼 %s" % bone)
		return null
	var attach := BoneAttachment3D.new()
	attach.name = String(bone) + "_Attach"
	attach.bone_name = bone
	skeleton.add_child(attach)
	var socket := Node3D.new()
	socket.name = socket_name
	attach.add_child(socket)
	socket.transform = skeleton.get_bone_global_rest(idx).affine_inverse() * offset if offset_in_skeleton_space else offset
	return socket

func _setup_katana() -> void:
	if scabbard_socket == null:
		return
	var katana := KATANA_SCENE.instantiate()
	katana_blade = katana.find_child("Blade_Mesh", true, false) as MeshInstance3D
	katana_scabbard = katana.find_child("Scabbard_Mesh", true, false) as MeshInstance3D
	for mi: MeshInstance3D in [katana_blade, katana_scabbard]:
		if mi == null:
			continue
		mi.owner = null
		mi.get_parent().remove_child(mi)
		scabbard_socket.add_child(mi)
		mi.transform = Transform3D.IDENTITY
		_apply_katana_material(mi)
	katana.free()
	if katana_blade:
		katana_blade.name = "Katana_Blade"
	if katana_scabbard:
		katana_scabbard.name = "Katana_Scabbard"
	# 两分件网格原点重合于鞘口，刀身在鞘内的位姿即与刀鞘相同
	sheathe_transform = Transform3D.IDENTITY

func _apply_katana_material(mi: MeshInstance3D) -> void:
	for i in mi.mesh.get_surface_count():
		var src := mi.get_active_material(i)
		var mat := ShaderMaterial.new()
		mat.shader = SHADER_TOON
		mat.set_shader_parameter("albedo_texture", src.albedo_texture if src is BaseMaterial3D else null)
		if src is BaseMaterial3D:
			mat.set_shader_parameter("albedo_color", (src as BaseMaterial3D).albedo_color)
		mat.set_shader_parameter("enable_face_pitch_clamp", false)
		mat.set_shader_parameter("enable_hair_specular", false)
		var outline := ShaderMaterial.new()
		outline.render_priority = 1
		outline.shader = SHADER_OUTLINE
		outline.set_shader_parameter("outline_color", OUTLINE_COLOR)
		outline.set_shader_parameter("outline_thickness", OUTLINE_THICKNESS_KATANA)
		outline.set_shader_parameter("distance_scaling", true)
		mat.next_pass = outline
		mi.set_surface_override_material(i, mat)

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

## 刀柄握心世界坐标（拔刀态 = 右手掌心；物理抓握断言用）
func get_grip_center_world() -> Vector3:
	if katana_blade == null:
		return global_position + Vector3.UP
	return katana_blade.global_transform * GRIP_CENTER_LOCAL

## 右手掌心世界坐标（握刀插槽原点即掌心）
func get_palm_center_world() -> Vector3:
	return hand_socket.global_position if hand_socket else global_position + Vector3.UP

# ==================== 拔刀 / 纳刀 插槽切换 ====================

func draw_sword(_instant: bool = true) -> void:
	if is_drawn or katana_blade == null or hand_socket == null:
		return
	is_drawn = true
	_mount_blade(hand_socket, hand_drawn_transform)
	blade_drawn_changed.emit(true)

func sheathe_sword(_instant: bool = true) -> void:
	if not is_drawn or katana_blade == null or scabbard_socket == null:
		return
	is_drawn = false
	_mount_blade(scabbard_socket, sheathe_transform)
	clear_trail()
	blade_drawn_changed.emit(false)

func _mount_blade(new_parent: Node3D, local_transform: Transform3D) -> void:
	if katana_blade.get_parent() != new_parent:
		katana_blade.get_parent().remove_child(katana_blade)
		new_parent.add_child(katana_blade)
	katana_blade.transform = local_transform

func get_katana_position() -> Vector3:
	return katana_blade.global_position if katana_blade else global_position + Vector3.UP
