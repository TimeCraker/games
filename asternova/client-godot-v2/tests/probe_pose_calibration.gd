extends SceneTree

## 姿态标定探针（窗口化）：对 6 种候选源→目标修正模式各渲染 walk + Slash3 单帧，
## 供肉眼判定正确模式后固化进 build_aster_animlib.gd。
##   godot --path client-godot-v2 -s tests/probe_pose_calibration.gd

const BONE_MAP := {
	"Root": "Root", "Hips": "Hip", "Spine": "Waist", "Chest": "Spine01", "UpperChest": "Spine02",
	"Neck": "NeckTwist01", "Head": "Head",
	"LeftShoulder": "L_Clavicle", "RightShoulder": "R_Clavicle",
	"LeftUpperArm": "L_Upperarm", "RightUpperArm": "R_Upperarm",
	"LeftLowerArm": "L_Forearm", "RightLowerArm": "R_Forearm",
	"LeftHand": "L_Hand", "RightHand": "R_Hand",
	"LeftUpperLeg": "L_Thigh", "RightUpperLeg": "R_Thigh",
	"LeftLowerLeg": "L_Calf", "RightLowerLeg": "R_Calf",
	"LeftFoot": "L_Foot", "RightFoot": "R_Foot",
	"LeftToes": "L_ToeBase", "RightToes": "R_ToeBase",
}
const SRC_PARENTS := {
	"Root": "", "Hips": "Root", "Spine": "Hips", "Chest": "Spine", "UpperChest": "Chest",
	"Neck": "UpperChest", "Head": "Neck",
	"LeftShoulder": "UpperChest", "RightShoulder": "UpperChest",
	"LeftUpperArm": "LeftShoulder", "RightUpperArm": "RightShoulder",
	"LeftLowerArm": "LeftUpperArm", "RightLowerArm": "RightUpperArm",
	"LeftHand": "LeftLowerArm", "RightHand": "RightLowerArm",
	"LeftUpperLeg": "Hips", "RightUpperLeg": "Hips",
	"LeftLowerLeg": "LeftUpperLeg", "RightLowerLeg": "RightUpperLeg",
	"LeftFoot": "LeftLowerLeg", "RightFoot": "RightLowerLeg",
	"LeftToes": "LeftFoot", "RightToes": "RightFoot",
}

var src_lib: AnimationLibrary
var dst_skel: Skeleton3D
var player: AnimationPlayer
var cam: Camera3D
var images: Dictionary = {}

func _initialize() -> void:
	root.size = Vector2i(1280, 720)
	var studio: Node3D = (load("res://scenes/lighting/endfield_lighting_studio.tscn") as PackedScene).instantiate()
	root.add_child(studio)
	var glb: PackedScene = load("res://models/aster/aster_assembled.glb")
	var holder: Node3D = Node3D.new()
	root.add_child(holder)
	var inst: Node = glb.instantiate()
	holder.add_child(inst)
	dst_skel = inst.find_children("*", "Skeleton3D", true, false)[0]
	var armature: Node = dst_skel.get_parent()
	player = AnimationPlayer.new()
	holder.add_child(player)
	player.root_node = player.get_path_to(armature)
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
	player.add_animation_library("", AnimationLibrary.new())  # 占位，模式库后续挂 ""
	src_lib = load("res://art/animations/ShooterLib.res")
	var melee: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	for n in ["Slash3"]:
		src_lib.add_animation(n, melee.get_animation(n))
	cam = Camera3D.new()
	root.add_child(cam)
	cam.position = Vector3(2.3, 1.15, 2.3)
	cam.look_at(Vector3(0, 0.95, 0))
	cam.fov = 40.0
	cam.make_current()
	_run()

func ticks(n: int) -> void:
	for i in n:
		await physics_frame

func snap(name: String) -> void:
	await RenderingServer.frame_post_draw
	images[name] = root.get_viewport().get_texture().get_image()

func _run() -> void:
	await ticks(5)
	# 直接装载生产 aster_animlib.res 目验各剪辑姿态
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	for old in player.get_animation_library_list():
		player.remove_animation_library(old)
	player.add_animation_library("", lib)
	for clip in ["idle", "LightWalking", "LightRunning", "Sprint", "Slash3"]:
		if not lib.has_animation(clip):
			print("SKIP " + clip)
			continue
		player.play(clip)
		await ticks(40)
		await snap("res_" + clip)
	for name: String in images:
		images[name].save_png(ProjectSettings.globalize_path("res://../art/render_previews/combat/_calib_%s.png" % name))
	print("CALIB_DONE n=%d" % images.size())
	quit(0)

func _build_variant(K: Quaternion, root_only: bool) -> AnimationLibrary:
	# V1_Dlocal/noYaw 胜出模式：pre = Aster 局部 rest；Hips 位置做父骨系修正
	var out_lib := AnimationLibrary.new()
	var d_local := {}
	var d_gr := {}
	for s: String in BONE_MAP:
		var bi := dst_skel.find_bone(BONE_MAP[s])
		d_local[s] = dst_skel.get_bone_rest(bi).basis.get_rotation_quaternion()
		d_gr[s] = dst_skel.get_bone_global_rest(bi).basis.get_rotation_quaternion()
	for anim_name in ["idle", "walk", "Slash3"]:
		var src: Animation = src_lib.get_animation(anim_name)
		var out := Animation.new()
		out.length = src.length
		out.step = src.step
		out.loop_mode = src.loop_mode
		for t: int in src.get_track_count():
			var bone := String(src.track_get_path(t).get_subname(0))
			if bone.is_empty() or not BONE_MAP.has(bone):
				continue
			var ttype := src.track_get_type(t)
			if ttype == Animation.TYPE_ROTATION_3D:
				var nt := out.add_track(Animation.TYPE_ROTATION_3D)
				out.track_set_path(nt, NodePath("Skeleton3D:%s" % BONE_MAP[bone]))
				for k: int in src.track_get_key_count(t):
					var time: float = src.track_get_key_time(t, k)
					var q: Quaternion = src.rotation_track_interpolate(t, time)
					out.rotation_track_insert_key(nt, time, d_local[bone] * q)
			elif ttype == Animation.TYPE_POSITION_3D and (bone == "Hips" or bone == "Root"):
				var nt := out.add_track(Animation.TYPE_POSITION_3D)
				out.track_set_path(nt, NodePath("Skeleton3D:%s" % BONE_MAP[bone]))
				var parent_r := Quaternion.IDENTITY
				if bone == "Hips":
					parent_r = d_gr["Root"]
				for k: int in src.track_get_key_count(t):
					var time: float = src.track_get_key_time(t, k)
					var p: Vector3 = src.position_track_interpolate(t, time)
					if bone == "Hips":
						p = parent_r.inverse() * (p * 0.9054)
					out.position_track_insert_key(nt, time, p)
		out_lib.add_animation(anim_name, out)
	return out_lib
