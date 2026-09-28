extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	# Wait one frame
	await process_frame
	await process_frame
	
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	print("CharacterAster rig:", rig)
	if rig:
		print("anim_player:", rig.anim_player)
		if rig.anim_player:
			var lib = rig.anim_player.get_animation_library("")
			print("All animations in anim_player:", lib.get_animation_list())
		print("anim_tree:", rig.anim_tree)
		if rig.anim_tree:
			print("anim_tree active:", rig.anim_tree.active)
			print("Current state:", rig.get_current_state_node())
			# Test speed = 2.4 m/s (Walk, same as user screenshot!)
			rig.set_locomotion_blend(2.4)
			for i in range(10):
				await physics_frame
			
			# Check skeleton bone poses
			var skel = rig.skeleton
			print("Skeleton:", skel)
			if skel:
				var hips_idx = skel.find_bone("DEF-hips")
				var spine_idx = skel.find_bone("DEF-spine")
				var thigh_l_idx = skel.find_bone("DEF-thigh.L")
				print("DEF-hips pose:", skel.get_bone_pose_position(hips_idx), "rot:", skel.get_bone_pose_rotation(hips_idx))
				print("DEF-spine pose:", skel.get_bone_pose_position(spine_idx), "rot:", skel.get_bone_pose_rotation(spine_idx))
				print("DEF-thigh.L pose:", skel.get_bone_pose_position(thigh_l_idx), "rot:", skel.get_bone_pose_rotation(thigh_l_idx))

	quit()
