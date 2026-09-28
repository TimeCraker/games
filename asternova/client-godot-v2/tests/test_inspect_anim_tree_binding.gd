extends SceneTree

func _init() -> void:
	var player = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(player)
	
	for i in range(10):
		await process_frame
		
	var rig = player.find_child("CharacterAster", true, false)
	var tree: AnimationTree = rig.find_child("AnimationTree", true, false)
	var player_anim: AnimationPlayer = rig.find_child("AnimationPlayer", true, false)
	
	print("CharacterAster path:", rig.get_path())
	print("AnimationPlayer path:", player_anim.get_path() if player_anim else "NULL")
	print("AnimationTree path:", tree.get_path() if tree else "NULL")
	if tree:
		print("AnimationTree anim_player property:", tree.anim_player)
		print("AnimationTree resolved player node:", tree.get_node_or_null(tree.anim_player))
		print("AnimationTree active:", tree.active)
		var pb = tree.get("parameters/SM/playback")
		print("AnimationTree SM playback:", pb)
		if pb:
			print("  current_node:", pb.get_current_node())
			print("  is_playing:", pb.is_playing())
			
	quit(0)
