extends SceneTree

func _initialize() -> void:
	var skel_scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = skel_scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]

	var shooter: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	var tpose_s: Animation = shooter.get_animation("tpose")
	
	const SRC_PARENTS := {
		"Root": "", "Hips": "Root", "Spine": "Hips", "Chest": "Spine", "UpperChest": "Chest",
		"LeftShoulder": "UpperChest", "RightShoulder": "UpperChest",
		"LeftUpperArm": "LeftShoulder", "RightUpperArm": "RightShoulder",
		"LeftLowerArm": "LeftUpperArm", "RightLowerArm": "RightUpperArm",
		"LeftHand": "LeftLowerArm", "RightHand": "RightLowerArm",
	}

	var s_local := {}
	for t in tpose_s.get_track_count():
		if tpose_s.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			var bname := String(tpose_s.track_get_path(t).get_subname(0))
			s_local[bname] = tpose_s.rotation_track_interpolate(t, 0.0).normalized()

	var s_gr := {}
	for b: String in SRC_PARENTS:
		var chain: Array[String] = []
		var curr: String = b
		while curr != "":
			chain.push_front(curr)
			curr = SRC_PARENTS[curr]
		var q := Quaternion.IDENTITY
		for node_b in chain:
			q = q * s_local.get(node_b, Quaternion.IDENTITY)
		s_gr[b] = q.normalized()

	print("=== 手臂全局 Rest 朝向检测 ===")
	# 检查源骨架 LeftUpperArm 骨骼方向（骨骼局部 Y 轴在世界中的朝向）
	var s_l_arm_dir: Vector3 = Basis(s_gr["LeftUpperArm"]).x
	print("Source LeftUpperArm X-axis (raw): ", s_l_arm_dir)
	print("Source LeftUpperArm Y-axis (raw): ", Basis(s_gr["LeftUpperArm"]).y)
	print("Source LeftUpperArm Z-axis (raw): ", Basis(s_gr["LeftUpperArm"]).z)

	var d_l_idx := skel.find_bone("L_Upperarm")
	var d_gt := skel.get_bone_global_rest(d_l_idx)
	print("Aster L_Upperarm X-axis: ", d_gt.basis.x)
	print("Aster L_Upperarm Y-axis: ", d_gt.basis.y)
	print("Aster L_Upperarm Z-axis: ", d_gt.basis.z)

	quit(0)
