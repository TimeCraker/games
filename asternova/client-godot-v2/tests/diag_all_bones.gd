extends SceneTree

func _initialize() -> void:
	var scene_res: PackedScene = load("res://scenes/entities/character_aster.tscn")
	var inst: Node = scene_res.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	root.add_child(inst)
	await process_frame
	await process_frame
	
	print("\n--- BONE GLOBAL POSES AT FRAME 1 ---")
	for i in range(skel.get_bone_count()):
		var bname = skel.get_bone_name(i)
		var rest_p = skel.get_bone_global_rest(i).origin
		var pose_p = skel.get_bone_global_pose(i).origin
		var diff = pose_p - rest_p
		if diff.length() > 0.01:
			print("%-20s rest=%s pose=%s diff=%.3f" % [bname, rest_p, pose_p, diff.length()])
	quit(0)
