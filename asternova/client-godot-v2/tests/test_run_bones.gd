@tool
extends SceneTree

func _init() -> void:
	var player_scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(player_scene)
	for i in range(5):
		await process_frame
	
	var rig: AsterRig = player_scene.visual_root.get_node("CharacterAster")
	var skel: Skeleton3D = rig.find_child("Skeleton3D", true, false)
	
	# Set locomotion to 6.5 m/s
	rig.set_locomotion_blend(6.5)
	
	for i in range(20):
		await physics_frame
		
	var head_idx = skel.find_bone("Head")
	var hip_idx = skel.find_bone("Hip")
	var foot_l = skel.find_bone("L_Foot")
	var foot_r = skel.find_bone("R_Foot")
	
	print("At 6.5m/s run:")
	print("  Hip global pos: ", skel.global_transform * skel.get_bone_global_pose(hip_idx).origin)
	print("  Head global pos: ", skel.global_transform * skel.get_bone_global_pose(head_idx).origin)
	print("  L_Foot global pos: ", skel.global_transform * skel.get_bone_global_pose(foot_l).origin)
	print("  R_Foot global pos: ", skel.global_transform * skel.get_bone_global_pose(foot_r).origin)
	
	# Check head vs hip Z offset (is head in front of hip or behind?)
	var head_pos = skel.global_transform * skel.get_bone_global_pose(head_idx).origin
	var hip_pos = skel.global_transform * skel.get_bone_global_pose(hip_idx).origin
	print("  Head.z - Hip.z: ", head_pos.z - hip_pos.z)
	
	quit(0)
