extends SceneTree

func _initialize() -> void:
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	if lib == null:
		print("Failed to load aster_animlib.res")
		quit(1)
		return
	print("Loaded aster_animlib.res successfully!")
	print("Animations count: ", lib.get_animation_list().size())
	
	for name in ["idle", "LightIdle", "Walk", "Sword_Idle"]:
		if not lib.has_animation(name):
			print("Missing anim: ", name)
			continue
		var anim: Animation = lib.get_animation(name)
		print("Anim: ", name, " length: ", anim.length, " tracks: ", anim.get_track_count())
		for t in anim.get_track_count():
			var p: String = anim.track_get_path(t)
			if "Upperarm" in p or "Forearm" in p or "Hand" in p or "Thigh" in p or "Waist" in p or "Pelvis" in p:
				var key_count = anim.track_get_key_count(t)
				var val0 = anim.track_get_key_value(t, 0)
				print("  Track: ", p, " keys: ", key_count, " val[0]: ", val0)
	quit(0)
