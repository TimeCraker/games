extends SceneTree

func _init() -> void:
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose: Animation = melee_lib.get_animation("TPose")
	print("=== MeleeLib TPose 姿态审计 ===")
	for t in tpose.get_track_count():
		var path = tpose.track_get_path(t)
		var bname = String(path.get_subname(0))
		if bname in ["Hips", "LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "RightLowerLeg", "LeftFoot", "RightFoot", "LeftUpperArm", "RightUpperArm"]:
			var q: Quaternion = tpose.rotation_track_interpolate(t, 0.0)
			var euler: Vector3 = q.get_euler() * (180.0 / PI)
			print("  Bone: %-15s Euler: (x=%6.1f, y=%6.1f, z=%6.1f)" % [bname, euler.x, euler.y, euler.z])
	quit(0)
