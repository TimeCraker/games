extends SceneTree

func _initialize() -> void:
	var lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	for anim_name in ["idle", "LightIdle", "LightWalking", "LightRunning"]:
		var anim: Animation = lib.get_animation(anim_name) if lib.has_animation(anim_name) else null
		if anim == null:
			continue
		print("\n=== Clip: ", anim_name, " ===")
		for t in anim.get_track_count():
			var p := anim.track_get_path(t)
			var bname := String(p.get_subname(0))
			if "arm" in bname.to_lower() or "hand" in bname.to_lower() or "leg" in bname.to_lower() or "thigh" in bname.to_lower():
				if anim.track_get_type(t) == Animation.TYPE_ROTATION_3D:
					var q := anim.rotation_track_interpolate(t, 0.0)
					print("  %-16s: rot=%s angle=%.1f deg" % [bname, q, rad_to_deg(q.get_angle())])
	quit(0)
