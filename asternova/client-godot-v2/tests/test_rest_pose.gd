extends SceneTree

func _initialize() -> void:
	print("=== Test CharacterAster Rest Pose (No Animation) ===")
	var scene_res: PackedScene = load("res://scenes/levels/combat_playground.tscn")
	var scene := scene_res.instantiate()
	root.add_child(scene)
	
	var player := scene.get_node("Player")
	var rig: AsterRig = player.get_node("VisualRoot/CharacterAster")
	
	# 彻底关闭 AnimationTree 和 AnimationPlayer
	if rig.anim_tree:
		rig.anim_tree.active = false
	if rig.anim_player:
		rig.anim_player.stop()
	
	var skel: Skeleton3D = rig.find_child("Skeleton3D", true, false)
	if skel:
		skel.reset_bone_poses()
	
	# 等待 10 帧
	for f in 10:
		await process_frame
	
	# 检查骨骼是否全部复位为 Rest 姿态
	var r_upper := skel.find_bone("R_Upperarm")
	var r_fore := skel.find_bone("R_Forearm")
	var r_hand := skel.find_bone("R_Hand")
	var l_thigh := skel.find_bone("L_Thigh")
	var r_thigh := skel.find_bone("R_Thigh")
	
	print("R_Upperarm global origin: ", skel.get_bone_global_pose(r_upper).origin)
	print("R_Forearm  global origin: ", skel.get_bone_global_pose(r_fore).origin)
	print("R_Hand     global origin: ", skel.get_bone_global_pose(r_hand).origin)
	print("L_Thigh    rot euler deg: ", rad_to_deg(skel.get_bone_pose_rotation(l_thigh).get_euler().y))
	print("R_Thigh    rot euler deg: ", rad_to_deg(skel.get_bone_pose_rotation(r_thigh).get_euler().y))
	
	quit(0)
