extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	root.add_child(inst)

	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	print("Bone count: ", skel.get_bone_count())
	for bname in ["Root", "Hip", "Pelvis", "L_Foot", "R_Foot", "L_ToeBase", "R_ToeBase"]:
		var idx := skel.find_bone(bname)
		if idx >= 0:
			var gr := skel.get_bone_global_rest(idx)
			print("REST Global %-12s: origin=%s" % [bname, gr.origin.snapped(Vector3(0.001,0.001,0.001))])

	var anim_player: AnimationPlayer = inst.find_child("AnimationPlayer", true, false)
	if anim_player:
		print("Animations in GLB AnimationPlayer:")
		var lib := anim_player.get_animation_library("")
		for a in lib.get_animation_list():
			var anim := lib.get_animation(a)
			print("  anim: %s (len=%.2fs, tracks=%d)" % [a, anim.length, anim.get_track_count()])
			# 检查这个动作下 Hip 和 Foot 的高度
			anim_player.play(a)
			anim_player.advance(0.0)
			# 查看骨骼 pose
			var hip_idx = skel.find_bone("Hip")
			var l_foot_idx = skel.find_bone("L_Foot")
			var r_foot_idx = skel.find_bone("R_Foot")
			print("    at t=0: Hip pose pos=%s, L_Foot rest pos=%s" % [
				skel.get_bone_pose_position(hip_idx),
				skel.get_bone_rest(l_foot_idx).origin
			])
			# 检查动画轨道是否有 position 轨道
			for t in anim.get_track_count():
				if anim.track_get_type(t) == Animation.TYPE_POSITION_3D:
					print("    track pos: %s" % anim.track_get_path(t))

	inst.free()
	quit(0)
