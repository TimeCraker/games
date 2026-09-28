extends SceneTree

func _init() -> void:
	var player_scene = load("res://scenes/entities/player.tscn")
	var player = player_scene.instantiate()
	root.add_child(player)
	
	# Wait for ready and physics frames
	for i in range(10):
		await physics_frame
		
	var skel: Skeleton3D = player.find_child("Skeleton3D", true, false)
	if not skel:
		print("ERROR: Skeleton3D not found!")
		quit(1)
		return
		
	print("Skeleton bone count:", skel.get_bone_count())
	print("\n--- LEG BONE RUNTIME POSE TRANSFORMS ---")
	var leg_bones = [
		"DEF-hips",
		"DEF-thigh.L", "DEF-shin.L", "DEF-foot.L", "DEF-toe.L",
		"DEF-thigh.R", "DEF-shin.R", "DEF-foot.R", "DEF-toe.R"
	]
	for bname in leg_bones:
		var idx = skel.find_bone(bname)
		if idx == -1:
			print("Bone not found:", bname)
			continue
		var rest = skel.get_bone_rest(idx)
		var pose = skel.get_bone_pose(idx)
		var global_pose = skel.get_bone_global_pose(idx)
		print("%-14s | idx=%2d | global_pos=(%+.3f,%+.3f,%+.3f) | pose_scale=(%+.3f,%+.3f,%+.3f) | rest_pos=(%+.3f,%+.3f,%+.3f)" % [
			bname, idx,
			global_pose.origin.x, global_pose.origin.y, global_pose.origin.z,
			pose.basis.get_scale().x, pose.basis.get_scale().y, pose.basis.get_scale().z,
			rest.origin.x, rest.origin.y, rest.origin.z
		])

	# Also check Aster_Body skin and mesh
	var mesh_inst: MeshInstance3D = player.find_child("Aster_Body", true, false)
	if mesh_inst:
		print("\nAster_Body found:")
		print("  transform:", mesh_inst.transform)
		print("  skin:", mesh_inst.skin)
		if mesh_inst.skin:
			print("  skin bind count:", mesh_inst.skin.get_bind_count())
			for i in range(mini(5, mesh_inst.skin.get_bind_count())):
				var b_name = mesh_inst.skin.get_bind_name(i)
				var b_bone = mesh_inst.skin.get_bind_bone(i)
				print("    bind %d: name='%s' bone_idx=%d" % [i, b_name, b_bone])
	else:
		print("Aster_Body mesh instance NOT found under player!")
		
	quit(0)
