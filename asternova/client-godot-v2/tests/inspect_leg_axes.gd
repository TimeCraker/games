extends SceneTree

func _initialize() -> void:
	print("=== Detailed Source TPose Bone Axes ===")
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose: Animation = melee_lib.get_animation("TPose")
	
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
	
	for bone in ["LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot"]:
		var q: Quaternion = composed[bone]
		var b := Basis(q)
		print("%-15s: x=%s, y=%s, z=%s" % [bone, b.x, b.y, b.z])
	
	quit(0)
