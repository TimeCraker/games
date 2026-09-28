extends SceneTree

func _initialize() -> void:
	var slib: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	var anim: Animation = slib.get_animation("idle")
	var tpose: Animation = slib.get_animation("tpose")
	
	var track_anim := -1
	var track_tpose := -1
	for t in anim.get_track_count():
		if "RightUpperArm" in String(anim.track_get_path(t)) and anim.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			track_anim = t
	for t in tpose.get_track_count():
		if "RightUpperArm" in String(tpose.track_get_path(t)) and tpose.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			track_tpose = t
		
	var s_local: Quaternion = anim.rotation_track_interpolate(track_anim, 0.0).normalized()
	var s_calib: Quaternion = tpose.rotation_track_interpolate(track_tpose, 0.0).normalized()
	
	print("s_calib * RIGHT:", s_calib * Vector3.RIGHT, " s_calib * UP:", s_calib * Vector3.UP)
	print("s_local * RIGHT:", s_local * Vector3.RIGHT, " s_local * UP:", s_local * Vector3.UP)
	
	# The Delta:
	var delta := s_local * s_calib.inverse()
	print("delta * RIGHT:", delta * Vector3.RIGHT)
	print("delta * UP:", delta * Vector3.UP)
	quit(0)
