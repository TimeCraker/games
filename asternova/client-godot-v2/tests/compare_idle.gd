extends SceneTree

func _initialize() -> void:
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var aster_lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	
	var src_idle := melee_lib.get_animation("idle")
	var dst_idle := aster_lib.get_animation("idle")
	
	print("--- SRC IDLE TRACKS ---")
	for t in src_idle.get_track_count():
		var path = str(src_idle.track_get_path(t))
		if "Hips" in path or "Spine" in path:
			print(path, " val@0=", src_idle.rotation_track_interpolate(t, 0.0))
			
	print("--- DST IDLE TRACKS ---")
	for t in dst_idle.get_track_count():
		var path = str(dst_idle.track_get_path(t))
		if "Hip" in path or "Waist" in path:
			print(path, " val@0=", dst_idle.rotation_track_interpolate(t, 0.0))
	quit(0)
