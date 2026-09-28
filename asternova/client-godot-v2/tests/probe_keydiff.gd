extends SceneTree
## 对比 idle(标定基准) vs 其他 take 的 Root/Hip/Spine 键差角——验证系统性根骨偏转假设
func _initialize() -> void:
	var shooter: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	var melee: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	for pair in [["Shooter", shooter, "idle", ["walk", "run_067", "jump", "fall"]],
			["Melee", melee, "LightIdle", ["LightWalking", "Sprint", "Slash1", "LightRunning"]]]:
		var lib: AnimationLibrary = pair[1]
		var base: Animation = lib.get_animation(pair[2])
		var base_q := {}
		for t: int in base.get_track_count():
			if base.track_get_type(t) == Animation.TYPE_ROTATION_3D:
				base_q[String(base.track_get_path(t).get_subname(0))] = base.rotation_track_interpolate(t, 0.0)
		for take_name: String in pair[3]:
			if not lib.has_animation(take_name):
				continue
			var take: Animation = lib.get_animation(take_name)
			var diffs := {}
			for t: int in take.get_track_count():
				if take.track_get_type(t) != Animation.TYPE_ROTATION_3D:
					continue
				var bn := String(take.track_get_path(t).get_subname(0))
				if not base_q.has(bn) or not bn in ["Root", "Hip", "Spine", "Chest", "UpperChest", "Hips", "Spine01", "Spine02"]:
					continue
				var q1: Quaternion = take.rotation_track_interpolate(t, 0.0)
				var ang := rad_to_deg(q1.angle_to(base_q[bn]))
				diffs[bn] = ang
			print("%s %s vs %s: %s" % [pair[0], take_name, pair[2], str(diffs)])
	quit(0)
