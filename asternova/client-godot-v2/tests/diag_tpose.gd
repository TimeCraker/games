extends SceneTree

func _initialize() -> void:
	var mlib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var anim: Animation = mlib.get_animation("TPose")
	print("TPose length=", anim.length, " tracks=", anim.get_track_count())
	for t in range(anim.get_track_count()):
		var path = anim.track_get_path(t)
		var s = String(path)
		if "Arm" in s or "Hand" in s or "Shoulder" in s:
			print("  ", path, " key0=", anim.track_get_key_value(t, 0))
	quit(0)
