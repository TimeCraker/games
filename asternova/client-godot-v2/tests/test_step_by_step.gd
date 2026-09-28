extends SceneTree

func _initialize() -> void:
	print("=== Test CharacterAster Step by Step ===")
	var scene_res: PackedScene = load("res://scenes/entities/character_aster.tscn")
	var inst: Node = scene_res.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	var rh := skel.find_bone("R_Hand")
	
	print("1. After instantiate (before enter tree): R_Hand global pos = ", skel.get_bone_global_pose(rh).origin)
	
	root.add_child(inst)
	print("2. Immediately after enter tree (_ready called): R_Hand global pos = ", skel.get_bone_global_pose(rh).origin)
	
	for f in 5:
		await process_frame
		print("3. Frame %d: R_Hand global pos = %s" % [f, skel.get_bone_global_pose(rh).origin])
	
	quit(0)
