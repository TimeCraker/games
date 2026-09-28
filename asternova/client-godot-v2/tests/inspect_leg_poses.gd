extends SceneTree

func _initialize() -> void:
	var skel_scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = skel_scene.instantiate()
	root.add_child(inst)
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	var arm: Node = skel.get_parent()
	
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	var player := AnimationPlayer.new()
	arm.add_child(player)
	player.root_node = NodePath("..")
	player.add_animation_library("", lib)
	
	var test_clips := ["idle", "LightIdle", "LightWalking", "LightRunning", "Slash1"]
	for clip in test_clips:
		if not player.has_animation(clip):
			print("Missing clip: ", clip)
			continue
		player.play(clip)
		player.advance(0.01)
		print("\n=== Pose for clip: ", clip, " ===")
		for bname in ["Hip", "L_Thigh", "R_Thigh", "L_Calf", "R_Calf", "L_Foot", "R_Foot"]:
			var idx := skel.find_bone(bname)
			if idx < 0:
				print("Missing bone: ", bname)
				continue
			var gp := skel.get_bone_global_pose(idx)
			var rot := gp.basis.get_euler()
			print("  %-8s: pos=(%6.3f, %6.3f, %6.3f), rot_deg=(%6.1f, %6.1f, %6.1f)" % [
				bname, gp.origin.x, gp.origin.y, gp.origin.z,
				rad_to_deg(rot.x), rad_to_deg(rot.y), rad_to_deg(rot.z)
			])
	quit(0)
