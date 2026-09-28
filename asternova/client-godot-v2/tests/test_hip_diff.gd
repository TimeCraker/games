extends SceneTree

func _initialize() -> void:
	var path := "res://../test_hip.glb"
	var scene: PackedScene = load(path)
	var inst: Node = scene.instantiate()
	var anim_player: AnimationPlayer = inst.find_child("AnimationPlayer", true, false)
	var lib = anim_player.get_animation_library("")
	var anim = lib.get_animation("test")
	for t in anim.get_track_count():
		if anim.track_get_type(t) == Animation.TYPE_POSITION_3D:
			print("Track pos path: ", anim.track_get_path(t))
			print("  val at 0.0: ", anim.position_track_interpolate(t, 0.0))
	inst.free()
	quit(0)
