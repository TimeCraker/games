extends SceneTree

func _initialize() -> void:
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	for clip in ["idle", "LightIdle", "LightWalking", "LightRunning", "Slash1"]:
		if not lib.has_animation(clip):
			print("No clip: ", clip)
			continue
		var anim: Animation = lib.get_animation(clip)
		print("\nClip: ", clip, " length=", anim.length, " tracks=", anim.get_track_count())
		for t in anim.get_track_count():
			var path := String(anim.track_get_path(t))
			if "Thigh" in path or "Calf" in path or "Foot" in path:
				var k_count := anim.track_get_key_count(t)
				var k0 = anim.rotation_track_interpolate(t, 0.0) if anim.track_get_type(t) == Animation.TYPE_ROTATION_3D else null
				var k_mid = anim.rotation_track_interpolate(t, anim.length * 0.5) if anim.track_get_type(t) == Animation.TYPE_ROTATION_3D else null
				print("  Track: ", path, " keys=", k_count, " k0=", k0, " k_mid=", k_mid)
	quit(0)
