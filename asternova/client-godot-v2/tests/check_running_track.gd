extends SceneTree

func _initialize() -> void:
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	var anim: Animation = lib.get_animation("LightRunning")
	print("LightRunning length: ", anim.length)
	for t in anim.get_track_count():
		var p = str(anim.track_get_path(t))
		if "Hip" in p or "Waist" in p or "Spine" in p or "Thigh" in p:
			var q: Quaternion = anim.rotation_track_interpolate(t, 0.0)
			var b := Basis(q)
			print(p, " rot_deg=", b.get_euler() * 180.0 / PI)
	quit(0)
