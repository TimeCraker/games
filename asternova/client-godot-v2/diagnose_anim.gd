extends SceneTree

func _init() -> void:
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var anim: Animation = melee_lib.get_animation("idle")
	if anim == null:
		anim = melee_lib.get_animation("LightIdle")
	print("Found anim: ", anim != null, " length=", anim.length if anim else 0)
	
	# 查看 LeftUpperLeg, RightUpperLeg, LeftLowerLeg, RightLowerLeg 的旋转
	for t in anim.get_track_count():
		var path = anim.track_get_path(t)
		var bname = String(path.get_subname(0))
		if bname in ["LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "RightLowerLeg", "LeftFoot", "RightFoot"]:
			var q0: Quaternion = anim.rotation_track_interpolate(t, 0.0)
			print("  Src Track ", bname, " key0=", q0, " euler_deg=", q0.get_euler() * (180.0 / PI))
			
	# 检查 Aster 重定向库中的对应轨道
	var aster_lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	var aster_anim: Animation = aster_lib.get_animation("idle")
	if aster_anim == null:
		aster_anim = aster_lib.get_animation("LightIdle")
	print("\nAster Retargeted anim:")
	for t in aster_anim.get_track_count():
		var path = aster_anim.track_get_path(t)
		var bname = String(path.get_subname(0))
		if bname in ["L_Thigh", "R_Thigh", "L_Calf", "R_Calf", "L_Foot", "R_Foot"]:
			var q0: Quaternion = aster_anim.rotation_track_interpolate(t, 0.0)
			print("  Dst Track ", bname, " key0=", q0, " euler_deg=", q0.get_euler() * (180.0 / PI))
			
	quit(0)
