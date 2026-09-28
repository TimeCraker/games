extends SceneTree
## 无头组合扫描：旋转前因子变体 × 180° yaw 变体，对 walk 做数值判据筛选。
## 判据：髋部世界高 0.75~1.0；头 > 1.3；双脚 x 分居两侧；手部摆动主轴为 Z 向（前后摆）。

const MAP := {
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

var dst_skel: Skeleton3D
var player: AnimationPlayer
var holder: Node3D

func _initialize() -> void:
	var glb: PackedScene = load("res://models/aster/aster_assembled.glb")
	holder = Node3D.new()
	root.add_child(holder)
	var inst: Node = glb.instantiate()
	holder.add_child(inst)
	dst_skel = inst.find_children("*", "Skeleton3D", true, false)[0]
	player = AnimationPlayer.new()
	holder.add_child(player)
	player.root_node = player.get_path_to(dst_skel.get_parent())
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
	_scan()

func ticks(n: int) -> void:
	for i in n:
		await physics_frame

func _scan() -> void:
	await ticks(3)
	var src_lib: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var d_gr := {}      # 骨架系全局 rest 旋转
	var d_gr_local := {} # 局部 rest 旋转
	for s: String in MAP:
		var i := dst_skel.find_bone(MAP[s])
		d_gr[s] = dst_skel.get_bone_global_rest(i).basis.get_rotation_quaternion()
		d_gr_local[s] = dst_skel.get_bone_rest(i).basis.get_rotation_quaternion()
	var yaw180 := Quaternion(Vector3.UP, PI)
	# 源全局 rest 自标定 v2：每库用自己的 idle 系剪辑（两库来源不同，约定不同）
	var s_gr_shooter := {}
	var idle_shooter: Animation = src_lib.get_animation("idle")
	for t: int in idle_shooter.get_track_count():
		if idle_shooter.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			var bn := String(idle_shooter.track_get_path(t).get_subname(0))
			if MAP.has(bn):
				s_gr_shooter[bn] = idle_shooter.rotation_track_interpolate(t, 0.0)
	var s_gr_melee := {}
	var idle_melee: Animation = melee_lib.get_animation("LightIdle")
	for t: int in idle_melee.get_track_count():
		if idle_melee.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			var bn := String(idle_melee.track_get_path(t).get_subname(0))
			if MAP.has(bn):
				s_gr_melee[bn] = idle_melee.rotation_track_interpolate(t, 0.0)
	var SRC_PARENTS := {
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
	var s_gr_global_shooter := {}
	for s: String in SRC_PARENTS:
		var parent: String = SRC_PARENTS[s]
		s_gr_global_shooter[s] = (s_gr_global_shooter[parent] if parent != "" else Quaternion.IDENTITY) * s_gr_shooter.get(s, Quaternion.IDENTITY)
	var s_gr_global_melee := {}
	for s: String in SRC_PARENTS:
		var parent: String = SRC_PARENTS[s]
		s_gr_global_melee[s] = (s_gr_global_melee[parent] if parent != "" else Quaternion.IDENTITY) * s_gr_melee.get(s, Quaternion.IDENTITY)

	var variants := {
		"V7_idle": "idle",
	}
	for vname: String in variants:
		for yaw_name: String in ["noYaw", "yaw180"]:
			var use_yaw: bool = yaw_name == "yaw180"
			var lib := _build(src_lib, melee_lib, variants[vname], use_yaw, d_gr, d_gr_local, yaw180,
					s_gr_global_shooter, s_gr_global_melee)
			for old in player.get_animation_library_list():
				player.remove_animation_library(old)
			player.add_animation_library("", lib)
			# 依次验证 idle / LightIdle / LightWalking / Sprint 的直立性
			for clip in ["idle", "LightIdle", "LightWalking", "Sprint"]:
				player.play(clip)
				await ticks(45)
				var hand_samples: Array[Vector3] = []
				var hip_y := 0.0
				var head_y := 0.0
				var foot_l_x := 0.0
				var foot_r_x := 0.0
				var foot_min_y := 9.9
				var facing_sum := Vector3.ZERO
				for s in 14:
					await ticks(2)
					hand_samples.append(dst_skel.global_transform * dst_skel.get_bone_global_pose(dst_skel.find_bone("L_Hand")).origin)
					hip_y = (dst_skel.global_transform * dst_skel.get_bone_global_pose(dst_skel.find_bone("Hip")).origin).y
					head_y = (dst_skel.global_transform * dst_skel.get_bone_global_pose(dst_skel.find_bone("Head")).origin).y
					var fl: Vector3 = dst_skel.global_transform * dst_skel.get_bone_global_pose(dst_skel.find_bone("L_Foot")).origin
					var fr: Vector3 = dst_skel.global_transform * dst_skel.get_bone_global_pose(dst_skel.find_bone("R_Foot")).origin
					foot_l_x = fl.x
					foot_r_x = fr.x
					foot_min_y = minf(foot_min_y, minf(fl.y, fr.y))
					var pl: Vector3 = dst_skel.global_transform * dst_skel.get_bone_global_pose(dst_skel.find_bone("L_Upperarm")).origin
					var pr: Vector3 = dst_skel.global_transform * dst_skel.get_bone_global_pose(dst_skel.find_bone("R_Upperarm")).origin
					facing_sum += Vector3.UP.cross(pr - pl).normalized()
				var facing := (facing_sum / 14.0).normalized()
				print("%s/%s hip=%.2f head=%.2f footMin=%.2f footLx=%+.2f footRx=%+.2f facing=%s" % [
					vname, clip, hip_y, head_y, foot_min_y, foot_l_x, foot_r_x, str(facing.snapped(Vector3(0.01,0.01,0.01)))])
	quit(0)

func _build(src_lib: AnimationLibrary, melee_lib: AnimationLibrary, pre_mode: String, use_yaw: bool, d_gr: Dictionary, d_gr_local: Dictionary, yaw180: Quaternion, s_gr_shooter: Dictionary, s_gr_melee: Dictionary) -> AnimationLibrary:
	var out_lib := AnimationLibrary.new()
	var anim_names := ["idle", "walk", "LightIdle", "LightWalking", "Sprint", "Slash3"]
	for anim_name in anim_names:
		var from_melee: bool = anim_name in ["LightIdle", "LightWalking", "Sprint", "Slash3"]
		var src: Animation = (melee_lib if from_melee else src_lib).get_animation(anim_name)
		if src == null:
			print("SKIP missing clip: " + anim_name)
			continue
		var s_gr_global: Dictionary = s_gr_melee if from_melee else s_gr_shooter
		var out := Animation.new()
		out.length = src.length
		out.step = src.step
		out.loop_mode = src.loop_mode
		for t: int in src.get_track_count():
			var bone := String(src.track_get_path(t).get_subname(0))
			if bone.is_empty() or not MAP.has(bone):
				continue
			if src.track_get_type(t) == Animation.TYPE_ROTATION_3D:
				var pre: Quaternion
				if pre_mode == "idle" or pre_mode == "idle_yaw":
					pre = d_gr[bone].inverse() * s_gr_global[bone]
				elif pre_mode == "rename":
					pre = Quaternion.IDENTITY
				elif pre_mode == "restconj":
					pre = d_gr_local[bone] * d_gr[bone].inverse()
				else:
					pre = d_gr[bone].inverse()
				var nt := out.add_track(Animation.TYPE_ROTATION_3D)
				out.track_set_path(nt, NodePath("Skeleton3D:%s" % MAP[bone]))
				for k: int in src.track_get_key_count(t):
					var time: float = src.track_get_key_time(t, k)
					var q: Quaternion = src.rotation_track_interpolate(t, time)
					if use_yaw:
						q = yaw180 * q * yaw180.inverse()
					out.rotation_track_insert_key(nt, time, pre * q)
			elif src.track_get_type(t) == Animation.TYPE_POSITION_3D and (bone == "Hips" or bone == "Root"):
				var nt := out.add_track(Animation.TYPE_POSITION_3D)
				out.track_set_path(nt, NodePath("Skeleton3D:%s" % MAP[bone]))
				# 父骨局部系修正：Hip 的父 = Root，p_local = R_Root_gr⁻¹ · (p_src·scale)
				var parent_r := Quaternion.IDENTITY
				if bone == "Hips":
					parent_r = dst_skel.get_bone_global_rest(dst_skel.find_bone("Root")).basis.get_rotation_quaternion()
				for k: int in src.track_get_key_count(t):
					var time: float = src.track_get_key_time(t, k)
					var p: Vector3 = src.position_track_interpolate(t, time)
					if bone == "Hips":
						p = parent_r.inverse() * (p * 0.9054)
					out.position_track_insert_key(nt, time, p)
		out_lib.add_animation(anim_name, out)
	return out_lib
