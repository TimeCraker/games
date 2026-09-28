extends SceneTree
## Inspect animation libraries: names, track paths, lengths. Usage:
## godot --headless --path client-godot-v2 -s tests/inspect_animlib.gd [res_path]

func _initialize() -> void:
	var paths: Array[String] = [
		"res://art/animations/MeleeLib.res",
		"res://art/animations/ShooterLib.res",
	]
	var arg := OS.get_cmdline_user_args()
	if arg.size() > 0:
		paths = [arg[0]]
	for p: String in paths:
		print("\n==== ", p, " ====")
		var lib: Resource = load(p)
		if lib == null:
			print("  LOAD FAILED")
			continue
		print("  class: ", lib.get_class())
		if lib is AnimationLibrary:
			var alist := (lib as AnimationLibrary).get_animation_list()
			print("  animations: ", alist.size())
			for i: int in alist.size():
				var a: Animation = (lib as AnimationLibrary).get_animation(alist[i])
				print("  [%d] %s  len=%.3fs loop=%d tracks=%d step=%.3f" % [
					i, alist[i], a.length, a.loop_mode, a.get_track_count(), a.step])
				if i == 0:
					for t: int in a.get_track_count():
						var tp := a.track_get_path(t)
						var key_hint := ""
						if a.track_get_type(t) == Animation.TYPE_POSITION_3D:
							key_hint = "pos0=%s" % str(a.position_track_interpolate(t, 0.0))
						elif a.track_get_type(t) == Animation.TYPE_ROTATION_3D:
							key_hint = "rot0=%s" % str(a.rotation_track_interpolate(t, 0.0))
						print("      track[%d] type=%d path=%s %s" % [t, a.track_get_type(t), tp, key_hint])
	quit(0)
