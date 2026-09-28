extends SceneTree

func _initialize() -> void:
	var glb_path := "res://models/aster/test_export_hip.glb"
	var scn: Node = load(glb_path).instantiate()
	var ap: AnimationPlayer = scn.find_child("AnimationPlayer", true, false)
	print("Anims in test glb: ", ap.get_animation_list())
	var anim: Animation = ap.get_animation("TestHipIdle")
	for t in range(anim.get_track_count()):
		var path := str(anim.track_get_path(t))
		if "Hip" in path:
			print("Track ", t, " path=", path, " type=", anim.track_get_type(t))
			for k in range(anim.track_get_key_count(t)):
				print("  key ", k, " val=", anim.track_get_key_value(t, k))
	quit(0)
