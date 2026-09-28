extends SceneTree

func _initialize() -> void:
	var lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var anim: Animation = lib.get_animation("LightRunning")
	for t in anim.get_track_count():
		var p = str(anim.track_get_path(t))
		if "Hips" in p or "Spine" in p or "Chest" in p:
			var q: Quaternion = anim.rotation_track_interpolate(t, 0.0)
			var b := Basis(q)
			print(p, " rot_deg=", b.get_euler() * 180.0 / PI)
	quit(0)
