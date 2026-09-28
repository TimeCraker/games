extends SceneTree

func _initialize() -> void:
	var shooter_lib: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var aster_lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")

	print("Checking animations in aster_animlib:")
	for anim_name in ["LightWalking", "LightRunning", "Sprint", "idle"]:
		if aster_lib.has_animation(anim_name):
			var anim: Animation = aster_lib.get_animation(anim_name)
			print("Anim: ", anim_name, " len: ", anim.length, " tracks: ", anim.get_track_count())
			# Check Hips and Spine rotation track values at t = 0.0, 0.2, 0.4
			for t in anim.get_track_count():
				var p := String(anim.track_get_path(t))
				if "Hip" in p or "Waist" in p or "Spine" in p:
					if anim.track_get_type(t) == Animation.TYPE_ROTATION_3D:
						var q0 := anim.rotation_track_interpolate(t, 0.0)
						var qmid := anim.rotation_track_interpolate(t, anim.length * 0.5)
						print("  track: ", p, " rot@0 euler deg: ", q0.get_euler() * 180.0 / PI, " rot@mid euler deg: ", qmid.get_euler() * 180.0 / PI)
	quit(0)
