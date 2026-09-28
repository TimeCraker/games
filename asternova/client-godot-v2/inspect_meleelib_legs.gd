extends SceneTree

func _init() -> void:
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	for anim_name in ["TPose", "LightIdle", "LightWalking", "LightRunning"]:
		var anim: Animation = melee_lib.get_animation(anim_name)
		if anim == null:
			continue
		print("\n=== MeleeLib 剪辑: %s (时长 %.2fs) ===" % [anim_name, anim.length])
		for bname in ["Hips", "LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "RightLowerLeg", "LeftFoot", "RightFoot"]:
			for t in anim.get_track_count():
				if anim.track_get_type(t) == Animation.TYPE_ROTATION_3D and String(anim.track_get_path(t).get_subname(0)) == bname:
					var q: Quaternion = anim.rotation_track_interpolate(t, 0.0)
					var e: Vector3 = q.get_euler() * (180.0 / PI)
					print("  %-15s: key0 euler=(x=%6.1f, y=%6.1f, z=%6.1f) q=%s" % [bname, e.x, e.y, e.z, q])
	quit(0)
