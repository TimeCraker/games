extends SceneTree
func _initialize() -> void:
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	var a: Animation = lib.get_animation("idle")
	print("idle len=%.2f tracks=%d" % [a.length, a.get_track_count()])
	for bn in ["Root", "Hip", "Waist", "L_Thigh", "Head"]:
		for tt in [Animation.TYPE_ROTATION_3D, Animation.TYPE_POSITION_3D]:
			var ti := a.find_track(NodePath("Skeleton3D:%s" % bn), tt)
			if ti >= 0:
				var n := a.track_get_key_count(ti)
				var v0 = a.rotation_track_interpolate(ti, 0.0) if tt == Animation.TYPE_ROTATION_3D else a.position_track_interpolate(ti, 0.0)
				print("  %s t%d keys=%d k0=%s" % [bn, tt, n, str(v0)])
	# 帧内 bounds：位置轨道范围
	var hi := a.find_track(NodePath("Skeleton3D:Hip"), Animation.TYPE_POSITION_3D)
	if hi >= 0:
		var mn := Vector3(9e9, 9e9, 9e9)
		var mx := -mn
		for k: int in a.track_get_key_count(hi):
			var p: Vector3 = a.position_track_interpolate(hi, a.track_get_key_time(hi, k))
			mn = mn.min(p); mx = mx.max(p)
		print("  Hip pos range min=%s max=%s" % [str(mn.snapped(Vector3(0.01,0.01,0.01))), str(mx.snapped(Vector3(0.01,0.01,0.01)))])
	quit(0)
