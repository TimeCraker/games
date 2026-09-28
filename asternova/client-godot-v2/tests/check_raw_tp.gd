extends SceneTree

func _initialize() -> void:
	var m_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose: Animation = m_lib.get_animation("TPose")
	
	const SRC_PARENTS := {
		"Root": "", "Hips": "Root", "Spine": "Hips", "Chest": "Spine", "UpperChest": "Chest",
		"LeftUpperLeg": "Hips", "RightUpperLeg": "Hips",
		"LeftLowerLeg": "LeftUpperLeg", "RightLowerLeg": "RightUpperLeg",
		"LeftFoot": "LeftLowerLeg", "RightFoot": "RightLowerLeg",
		"LeftUpperArm": "UpperChest", "RightUpperArm": "UpperChest"
	}

	var s_local := {}
	for t in tpose.get_track_count():
		if tpose.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			var bname := String(tpose.track_get_path(t).get_subname(0))
			s_local[bname] = tpose.rotation_track_interpolate(t, 0.0).normalized()

	print("=== RAW (未经过任何旋转) MeleeLib TPose ===")
	for b: String in SRC_PARENTS:
		var curr: String = b
		var chain: Array[String] = []
		while curr != "":
			chain.push_front(curr)
			curr = SRC_PARENTS[curr]
		var q := Quaternion.IDENTITY
		for node_b in chain:
			q = q * s_local.get(node_b, Quaternion.IDENTITY)
		var basis := Basis(q.normalized())
		print("Bone %-14s raw basis: X=%s Y=%s Z=%s" % [
			b, basis.x.snapped(Vector3(0.01,0.01,0.01)), basis.y.snapped(Vector3(0.01,0.01,0.01)), basis.z.snapped(Vector3(0.01,0.01,0.01))])

	quit(0)
