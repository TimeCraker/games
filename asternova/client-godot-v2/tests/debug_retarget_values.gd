extends SceneTree

func _initialize() -> void:
	print("=== Debug Retargeting Calculation for Right Arm ===")
	# 查看 aster_animlib.res 中的 LightIdle
	var aster_lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	var idle_anim: Animation = aster_lib.get_animation("LightIdle") if aster_lib.has_animation("LightIdle") else aster_lib.get_animation("idle")
	
	print("Loaded anim: ", idle_anim.resource_name, " length: ", idle_anim.length)
	for t in idle_anim.get_track_count():
		var path := idle_anim.track_get_path(t)
		var bname := String(path.get_subname(0))
		if bname in ["R_Upperarm", "R_Forearm", "R_Hand", "L_Thigh", "R_Thigh"]:
			var q := idle_anim.rotation_track_interpolate(t, 0.0)
			var eu := q.get_euler()
			print("%-12s: local rot=(%.1f, %.1f, %.1f) deg" % [bname, rad_to_deg(eu.x), rad_to_deg(eu.y), rad_to_deg(eu.z)])
	
	quit(0)
