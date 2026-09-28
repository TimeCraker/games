@tool
extends SceneTree

func _init() -> void:
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	var anim = lib.get_animation("LightRunning")
	# Find Hip track
	var hip_idx = -1
	for t in range(anim.get_track_count()):
		if "Hip" in str(anim.track_get_path(t)):
			hip_idx = t
			break
	if hip_idx != -1:
		print("Hip track type: ", anim.track_get_type(hip_idx))
		for k in range(min(5, anim.track_get_key_count(hip_idx))):
			print("  key ", k, " time: ", anim.track_get_key_time(hip_idx, k), " val: ", anim.track_get_key_value(hip_idx, k))
	quit(0)
