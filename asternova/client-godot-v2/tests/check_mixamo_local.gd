extends SceneTree

func _initialize() -> void:
	var m_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose: Animation = m_lib.get_animation("TPose")
	
	print("=== Mixamo TPose 局部四元数与欧拉角 ===")
	for t in tpose.get_track_count():
		if tpose.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			var bname := String(tpose.track_get_path(t).get_subname(0))
			if bname in ["Hips", "LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "RightLowerLeg", "LeftFoot", "RightFoot", "LeftUpperArm", "RightUpperArm"]:
				var q: Quaternion = tpose.rotation_track_interpolate(t, 0.0).normalized()
				var b := Basis(q)
				print("Bone %-14s local basis: X=%s Y=%s Z=%s" % [
					bname, b.x.snapped(Vector3(0.01,0.01,0.01)), b.y.snapped(Vector3(0.01,0.01,0.01)), b.z.snapped(Vector3(0.01,0.01,0.01))])

	quit(0)
