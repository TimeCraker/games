extends SceneTree

func _initialize() -> void:
	var skel_scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = skel_scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	
	var m_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose: Animation = m_lib.get_animation("TPose")
	
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
		s_gr[b] = q.normalized()

	for b in ["LeftUpperLeg", "RightUpperLeg", "LeftFoot", "RightFoot"]:
		var basis := Basis(s_gr[b])
		print("Source ", b, " rest basis in TPose:\n  X=", basis.x, "\n  Y=", basis.y, "\n  Z=", basis.z)

	for b in ["L_Thigh", "R_Thigh", "L_Foot", "R_Foot"]:
		var idx := skel.find_bone(b)
		var rest := skel.get_bone_global_rest(idx)
		print("Aster ", b, " rest basis:\n  X=", rest.basis.x, "\n  Y=", rest.basis.y, "\n  Z=", rest.basis.z)

	quit(0)
