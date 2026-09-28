extends SceneTree

func _init() -> void:
	var glb = load("res://models/aster/aster_character.glb").instantiate()
	var ap: AnimationPlayer = glb.find_child("AnimationPlayer", true, false)
	var a = ap.get_animation("Idle")
	for t in range(a.get_track_count()):
		var p = String(a.track_get_path(t))
		if "arm" in p.to_lower() or "hand" in p.to_lower():
			print("Track %2d: %-35s Type: %d Key 0: %s" % [t, p, a.track_get_type(t), a.track_get_key_value(t, 0)])
	quit()
