extends SceneTree

func _init() -> void:
	var packed: PackedScene = load("res://scenes/entities/player.tscn")
	var player = packed.instantiate()
	root.add_child(player)
	for i in range(10):
		await process_frame
	var rig = player.get_node_or_null("VisualRoot/CharacterAster")
	var blade = rig.katana_blade if rig else null
	var scab = rig.scabbard_socket.get_node_or_null("Katana_Scabbard") if rig and rig.scabbard_socket else null
	print("Player rig found: ", rig != null)
	if rig:
		print("Is drawn: ", rig.is_drawn)
		print("Blade parent: ", blade.get_parent().name if blade else "NULL")
		print("Blade global pos: ", blade.global_position if blade else "NULL")
		print("Scabbard global pos: ", scab.global_position if scab else "NULL")
		if blade and scab:
			print("Pos diff: ", (blade.global_position - scab.global_position).length())
			print("Rot diff: ", (blade.global_rotation - scab.global_rotation).length())
	quit()
