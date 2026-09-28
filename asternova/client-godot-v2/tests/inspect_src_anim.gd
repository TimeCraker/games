extends SceneTree

func _initialize() -> void:
	print("=== Inspect Source TPose Animation ===")
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var anim_name := "TPose"
	var anim: Animation = melee_lib.get_animation(anim_name)
	
	for t in anim.get_track_count():
		var path := anim.track_get_path(t)
		var bname := String(path.get_subname(0))
		if bname in ["Hips", "LeftUpperArm", "RightUpperArm", "LeftUpperLeg", "RightUpperLeg"]:
			if anim.track_get_type(t) == Animation.TYPE_ROTATION_3D:
				var q: Quaternion = anim.rotation_track_interpolate(t, 0.0)
				var eu := q.get_euler()
				print("%-15s: q=%s, deg=(%.1f, %.1f, %.1f)" % [bname, q, rad_to_deg(eu.x), rad_to_deg(eu.y), rad_to_deg(eu.z)])
	
	quit(0)
