extends SceneTree
func _initialize() -> void:
	var melee: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var shooter: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	for lib_name in [["Melee", melee], ["Shooter", shooter]]:
		var lib: AnimationLibrary = lib_name[1]
		for anim_name in lib.get_animation_list():
			if not anim_name.begins_with("root-"):
				continue
			var a: Animation = lib.get_animation(anim_name)
			for t in a.get_track_count():
				var path := a.track_get_path(t)
				if String(path.get_subname(0)) == "Root" and a.track_get_type(t) == Animation.TYPE_POSITION_3D:
					var n := a.track_get_key_count(t)
					if n >= 2:
						var p0: Vector3 = a.position_track_interpolate(t, 0.0)
						var p1: Vector3 = a.position_track_interpolate(t, a.length)
						var d := p1 - p0
						if d.length() > 0.05:
							print("%s/%s keys=%d disp=%s |d|=%.2f" % [lib_name[0], anim_name, n, str(d.snapped(Vector3(0.01,0.01,0.01))), d.length()])
					break
	quit(0)
