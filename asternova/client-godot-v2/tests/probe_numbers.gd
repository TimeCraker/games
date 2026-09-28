extends SceneTree
## 无头数值解剖：rest vs 映射键 vs 播放后实际局部/全局值，定位骨架塌缩根因。

var dst_skel: Skeleton3D
var player: AnimationPlayer

func _initialize() -> void:
	var glb: PackedScene = load("res://models/aster/aster_assembled.glb")
	var holder: Node3D = Node3D.new()
	root.add_child(holder)
	var inst: Node = glb.instantiate()
	holder.add_child(inst)
	dst_skel = inst.find_children("*", "Skeleton3D", true, false)[0]
	player = AnimationPlayer.new()
	holder.add_child(player)
	player.root_node = player.get_path_to(dst_skel.get_parent())
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS

	for b in ["Root", "Hip", "Pelvis", "L_Thigh"]:
		var i := dst_skel.find_bone(b)
		var rest := dst_skel.get_bone_rest(i)
		var gr := dst_skel.get_bone_global_rest(i)
		print("REST %s local_t=%s local_r=%s global_t=%s" % [b, str(rest.origin.snapped(Vector3(0.001,0.001,0.001))), str(rest.basis.get_rotation_quaternion()), str(gr.origin.snapped(Vector3(0.001,0.001,0.001)))])

	# 映射 walk（identity 源 rest）
	var src: Animation = load("res://art/animations/ShooterLib.res").get_animation("walk")
	var out := Animation.new()
	out.length = src.length
	out.step = src.step
	out.loop_mode = src.loop_mode
	for t: int in src.get_track_count():
		var bone := String(src.track_get_path(t).get_subname(0))
		var map := {"Root": "Root", "Hips": "Hip", "Spine": "Waist", "Chest": "Spine01", "UpperChest": "Spine02", "Neck": "NeckTwist01", "Head": "Head", "LeftShoulder": "L_Clavicle", "RightShoulder": "R_Clavicle", "LeftUpperArm": "L_Upperarm", "RightUpperArm": "R_Upperarm", "LeftLowerArm": "L_Forearm", "RightLowerArm": "R_Forearm", "LeftHand": "L_Hand", "RightHand": "R_Hand", "LeftUpperLeg": "L_Thigh", "RightUpperLeg": "R_Thigh", "LeftLowerLeg": "L_Calf", "RightLowerLeg": "R_Calf", "LeftFoot": "L_Foot", "RightFoot": "R_Foot", "LeftToes": "L_ToeBase", "RightToes": "R_ToeBase"}
		if bone.is_empty() or not map.has(bone):
			continue
		if src.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			var nt := out.add_track(Animation.TYPE_ROTATION_3D)
			out.track_set_path(nt, NodePath("Skeleton3D:%s" % map[bone]))
			var pre: Quaternion = dst_skel.get_bone_global_rest(dst_skel.find_bone(map[bone])).basis.get_rotation_quaternion().inverse()
			for k: int in src.track_get_key_count(t):
				out.rotation_track_insert_key(nt, src.track_get_key_time(t, k), pre * src.rotation_track_interpolate(t, src.track_get_key_time(t, k)))
		elif src.track_get_type(t) == Animation.TYPE_POSITION_3D and (bone == "Hips" or bone == "Root"):
			var nt := out.add_track(Animation.TYPE_POSITION_3D)
			out.track_set_path(nt, NodePath("Skeleton3D:%s" % map[bone]))
			for k: int in src.track_get_key_count(t):
				var p: Vector3 = src.position_track_interpolate(t, src.track_get_key_time(t, k))
				if bone == "Hips":
					p *= 0.9054
				out.position_track_insert_key(nt, src.track_get_key_time(t, k), p)
	var lib := AnimationLibrary.new()
	lib.add_animation("walk", out)
	player.add_animation_library("", lib)

	for bn in ["Root", "Hip"]:
		for tt in [Animation.TYPE_POSITION_3D, Animation.TYPE_ROTATION_3D]:
			var ti := out.find_track(NodePath("Skeleton3D:%s" % bn), tt)
			if ti >= 0:
				var n := out.track_get_key_count(ti)
				print("TRACK %s type=%d keys=%d k0_t=%.2f k0=%s" % [bn, tt, n, out.track_get_key_time(ti, 0),
					str(out.position_track_interpolate(ti, 0.0) if tt == Animation.TYPE_POSITION_3D else out.rotation_track_interpolate(ti, 0.0))])
	player.play("walk")
	_run()

func _run() -> void:
	for i in 40:
		await physics_frame
	for b in ["Root", "Hip", "L_Thigh", "L_Foot"]:
		var i := dst_skel.find_bone(b)
		print("POSED %s local_t=%s global_t=%s" % [b,
			str(dst_skel.get_bone_pose_position(i).snapped(Vector3(0.001,0.001,0.001))),
			str(dst_skel.get_bone_global_pose(i).origin.snapped(Vector3(0.001,0.001,0.001)))])
	quit(0)
