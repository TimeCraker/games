extends SceneTree

func _initialize() -> void:
	var path := "res://scenes/entities/character_aster.tscn"
	var rig: AsterRig = load(path).instantiate() as AsterRig
	get_root().add_child(rig)

	var sk: Skeleton3D = rig.find_child("Skeleton3D", true, false) as Skeleton3D
	var anim_player: AnimationPlayer = rig.anim_player
	print("rig.anim_player: ", anim_player)
	print("--- ANIMATION LIGHTRUNNING t=0.4s ---")
	for bname in ["Root", "Hip", "Pelvis", "Waist", "Spine01", "Spine02", "Head"]:
		var idx := sk.find_bone(bname)
		if idx != -1:
			var rest_g := sk.get_bone_global_rest(idx)
			print(bname, " global rest rot euler: ", rest_g.basis.get_euler() * 180.0 / PI, " origin: ", rest_g.origin)

	print("--- ANIMATION LIGHTRUNNING t=0.4s ---")
	if anim_player:
		print("Has LightRunning: ", anim_player.has_animation("LightRunning"))
		if anim_player.has_animation("LightRunning"):
			anim_player.play("LightRunning")
			anim_player.advance(0.4)
			for bname in ["Root", "Hip", "Pelvis", "Waist", "Spine01", "Spine02", "Head"]:
				var idx := sk.find_bone(bname)
				if idx != -1:
					var pose_g := sk.get_bone_global_pose(idx)
					var pose_l := sk.get_bone_pose_rotation(idx)
					print(bname, " global rot euler: ", pose_g.basis.get_euler() * 180.0 / PI, " origin: ", pose_g.origin)

	quit(0)
