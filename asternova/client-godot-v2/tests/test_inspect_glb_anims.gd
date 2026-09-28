extends SceneTree

func _init() -> void:
	var glb: PackedScene = load("res://models/aster/aster_character.glb")
	var inst = glb.instantiate()
	root.add_child(inst)
	
	var ap: AnimationPlayer = inst.get_node("AnimationPlayer")
	print("Animation list in aster_character.glb:")
	for anim_name in ap.get_animation_list():
		var a = ap.get_animation(anim_name)
		print("  Anim: %-25s len=%.2f tracks=%d" % [anim_name, a.length, a.get_track_count()])
		
	# Let's inspect tracks of Walk_Loop or Walk or Idle_Loop
	for inspect_name in ["Idle", "Walk", "Jog_Fwd"]:
		if ap.has_animation(inspect_name):
			print("\n--- Inspecting tracks of %s ---" % inspect_name)
			var a = ap.get_animation(inspect_name)
			for t in range(a.get_track_count()):
				var path = a.track_get_path(t)
				var type = a.track_get_type(t)
				if "hips" in String(path).to_lower() or "root" in String(path).to_lower() or "spine" in String(path).to_lower():
					print("  Track %d: %s (type %d) key_count=%d" % [t, path, type, a.track_get_key_count(t)])
					if a.track_get_key_count(t) > 0:
						print("    Key 0 value: %s" % [a.track_get_key_value(t, 0)])
						
	quit()
