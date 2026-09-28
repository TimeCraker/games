extends SceneTree

func _initialize() -> void:
	var scene_res: PackedScene = load("res://scenes/levels/combat_playground.tscn")
	var scene := scene_res.instantiate()
	root.add_child(scene)
	
	var player := scene.get_node("Player")
	var rig: AsterRig = player.get_node("VisualRoot/CharacterAster")
	var skel: Skeleton3D = rig.find_child("Skeleton3D", true, false)
	
	# 等待 60 帧
	for f in 60:
		await process_frame
	
	print("Rig current state after 60 frames: ", rig.get_current_state_node())
	print("Locomotion speed blend: ", rig.anim_tree.get("parameters/SM/Locomotion/blend_position"))
	
	var key_bones := [
		"Pelvis", "Hip", "Waist", "Spine01", "Spine02",
		"L_Clavicle", "R_Clavicle", "L_Upperarm", "R_Upperarm",
		"L_Forearm", "R_Forearm", "L_Hand", "R_Hand",
		"L_Thigh", "R_Thigh", "L_Calf", "R_Calf", "L_Foot", "R_Foot"
	]
	for bname in key_bones:
		var idx := skel.find_bone(bname)
		if idx == -1: continue
		var q_rot := skel.get_bone_pose_rotation(idx)
		var g_pose := skel.get_bone_global_pose(idx)
		var euler := q_rot.get_euler()
		print("%-12s: rot_deg=(%6.1f, %6.1f, %6.1f), g_origin=(%6.3f, %6.3f, %6.3f)" % [
			bname, rad_to_deg(euler.x), rad_to_deg(euler.y), rad_to_deg(euler.z),
			g_pose.origin.x, g_pose.origin.y, g_pose.origin.z
		])
	
	quit(0)
