extends SceneTree

func _initialize() -> void:
	var shooter_lib: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")

	for lib_pair in [["Shooter", shooter_lib], ["Melee", melee_lib]]:
		var lib_name: String = lib_pair[0]
		var lib: AnimationLibrary = lib_pair[1]
		for anim_name in ["LightRunning", "LightWalking", "run_067", "walk"]:
			if lib.has_animation(anim_name):
				var anim: Animation = lib.get_animation(anim_name)
				print(lib_name, " ", anim_name, " len: ", anim.length)
				for t in anim.get_track_count():
					var p := String(anim.track_get_path(t))
					if "Hips" in p or "Spine" in p:
						if anim.track_get_type(t) == Animation.TYPE_ROTATION_3D:
							var q0 := anim.rotation_track_interpolate(t, 0.0)
							print("  ", p, " rot@0: ", q0.get_euler() * 180.0 / PI)
	quit(0)
