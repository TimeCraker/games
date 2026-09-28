extends SceneTree

func _initialize() -> void:
	var skel_scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = skel_scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	
	var m_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose: Animation = m_lib.get_animation("TPose")
	
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

	var s_local_rest := {}
	for t in tpose.get_track_count():
		if tpose.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			var bname := String(tpose.track_get_path(t).get_subname(0))
			s_local_rest[bname] = tpose.rotation_track_interpolate(t, 0.0).normalized()

	var q_rot_180 := Quaternion(Vector3.UP, PI)
	var s_gr := {}
	for b in SRC_PARENTS:
		var chain: Array[String] = []
		var curr: String = b
		while curr != "":
			chain.push_front(curr)
			curr = SRC_PARENTS[curr]
		var q := Quaternion.IDENTITY
		for node_b in chain:
			q = q * s_local_rest.get(node_b, Quaternion.IDENTITY)
		# 经 180° Y 对齐
		s_gr[b] = (q_rot_180 * q.normalized() * q_rot_180.inverse()).normalized()

	print("=== 对比 MeleeLib TPose(180对齐后) 与 Aster 全局 rest 朝向 ===")
	for src_b in BONE_MAP:
		var dst_b: String = BONE_MAP[src_b]
		var idx := skel.find_bone(dst_b)
		if idx < 0:
			continue
		var dst_gt := skel.get_bone_global_rest(idx)
		var s_basis := Basis(s_gr[src_b])
		var d_basis := dst_gt.basis
		
		# 计算两个 Basis 之间的夹角
		var s_q: Quaternion = s_gr[src_b]
		var d_q: Quaternion = d_basis.get_rotation_quaternion()
		var dot: float = absf(s_q.dot(d_q))
		var angle: float = rad_to_deg(2.0 * acos(minf(dot, 1.0)))
		print("Bone %-14s -> %-14s 夹角=%.1f°" % [src_b, dst_b, angle])
		print("  Src: X=%s Y=%s Z=%s" % [s_basis.x.snapped(Vector3(0.01,0.01,0.01)), s_basis.y.snapped(Vector3(0.01,0.01,0.01)), s_basis.z.snapped(Vector3(0.01,0.01,0.01))])
		print("  Dst: X=%s Y=%s Z=%s" % [d_basis.x.snapped(Vector3(0.01,0.01,0.01)), d_basis.y.snapped(Vector3(0.01,0.01,0.01)), d_basis.z.snapped(Vector3(0.01,0.01,0.01))])

	quit(0)
