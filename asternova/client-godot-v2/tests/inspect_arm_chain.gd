extends SceneTree

func _initialize() -> void:
	var glb: PackedScene = load("res://models/aster/aster_character.glb")
	var inst := glb.instantiate()
	var skel: Skeleton3D = inst.find_child("Skeleton3D", true, false) as Skeleton3D
	
	var melee: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose_m: Animation = melee.get_animation("TPose")

	print("=== Aster Arm Rest Bases ===")
	for b in ["L_Clavicle", "L_Upperarm", "L_Forearm", "L_Hand", "R_Clavicle", "R_Upperarm", "R_Forearm", "R_Hand"]:
		var idx := skel.find_bone(b)
		var p_idx := skel.get_bone_parent(idx)
		var p_name := skel.get_bone_name(p_idx) if p_idx >= 0 else "None"
		var gr := skel.get_bone_global_rest(idx)
		var lr := skel.get_bone_rest(idx)
		print("%s (parent: %s):" % [b, p_name])
		print("  global_origin: %s" % gr.origin)
		print("  basis.y: %s, basis.x: %s, basis.z: %s" % [gr.basis.y, gr.basis.x, gr.basis.z])
		print("  local_rot_quat: %s" % lr.basis.get_rotation_quaternion())

	print("\n=== Mixamo TPose Arm Rotations ===")
	var q_rot_180 := Quaternion(Vector3.UP, PI)
	var local_m := {}
	for t in tpose_m.get_track_count():
		if tpose_m.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			var bname := String(tpose_m.track_get_path(t).get_subname(0))
			local_m[bname] = tpose_m.rotation_track_interpolate(t, 0.0).normalized()

	var SRC_PARENTS := {
		"Root": "", "Hips": "Root", "Spine": "Hips", "Chest": "Spine", "UpperChest": "Chest",
		"Neck": "UpperChest", "Head": "Neck",
		"LeftShoulder": "UpperChest", "RightShoulder": "UpperChest",
		"LeftUpperArm": "LeftShoulder", "RightUpperArm": "RightShoulder",
		"LeftLowerArm": "LeftUpperArm", "RightLowerArm": "RightUpperArm",
		"LeftHand": "LeftLowerArm", "RightHand": "RightLowerArm",
	}

	for b in ["LeftShoulder", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightShoulder", "RightUpperArm", "RightLowerArm", "RightHand"]:
		var chain: Array[String] = []
		var curr: String = b
		while curr != "":
			chain.push_front(curr)
			curr = SRC_PARENTS.get(curr, "")
		var q := Quaternion.IDENTITY
		for node_b in chain:
			q = q * local_m.get(node_b, Quaternion.IDENTITY)
		var sg_180: Quaternion = (q_rot_180 * q.normalized() * q_rot_180.inverse()).normalized()
		var b_basis := Basis(sg_180)
		print("%s in Mixamo TPose (rotated 180):" % b)
		print("  sg_180 quat: %s" % sg_180)
		print("  basis.y: %s, basis.x: %s, basis.z: %s" % [b_basis.y, b_basis.x, b_basis.z])

	quit(0)
