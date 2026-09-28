extends SceneTree

func _initialize() -> void:
	print("=== Source Skeleton TPose Basis ===")
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose: Animation = melee_lib.get_animation("TPose")
	
	# 合成源骨骼全局旋转
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
	
	var s_gr_local := {}
	for t: int in tpose.get_track_count():
		if tpose.track_get_type(t) != Animation.TYPE_ROTATION_3D: continue
		var bone := String(tpose.track_get_path(t).get_subname(0))
		s_gr_local[bone] = tpose.rotation_track_interpolate(t, 0.0)
	
	var composed := {}
	for src_bone: String in SRC_PARENTS:
		var parent: String = SRC_PARENTS[src_bone]
		var local: Quaternion = s_gr_local.get(src_bone, Quaternion.IDENTITY)
		composed[src_bone] = (composed[parent] if parent != "" else Quaternion.IDENTITY) * local
	
	# 打印源全局旋转四元数及其转换的基向量
	for bone in ["Hips", "Chest", "LeftUpperArm", "RightUpperArm", "LeftUpperLeg", "RightUpperLeg"]:
		var q: Quaternion = composed[bone]
		var b := Basis(q)
		print("\nSource TPose: ", bone)
		print("  basis.x = ", b.x)
		print("  basis.y = ", b.y)
		print("  basis.z = ", b.z)
		
		# 加上 q_rot_180 对齐后呢？
		var q_rot_180 := Quaternion(Vector3.UP, PI)
		var q_aligned: Quaternion = q_rot_180 * q * q_rot_180.inverse()
		var b_aligned := Basis(q_aligned)
		print("  [Aligned] basis.x = ", b_aligned.x)
		print("  [Aligned] basis.y = ", b_aligned.y)
		print("  [Aligned] basis.z = ", b_aligned.z)
	
	quit(0)
