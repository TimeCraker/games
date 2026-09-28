extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	var anim_player: AnimationPlayer = inst.find_child("AnimationPlayer", true, false)
	var lib = anim_player.get_animation_library("")
	var anim = lib.get_animation("LightIdle")
	for t in anim.get_track_count():
		if "Hip" in String(anim.track_get_path(t)):
			print("Track %d: path=%s, type=%d, keys=%d" % [t, anim.track_get_path(t), anim.track_get_type(t), anim.track_get_key_count(t)])
			for k in min(5, anim.track_get_key_count(t)):
				print("  key %d: val=%s" % [k, anim.track_get_key_value(t, k)])
	inst.free()
	quit(0)
