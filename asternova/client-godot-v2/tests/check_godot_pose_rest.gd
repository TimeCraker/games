extends SceneTree

func _initialize() -> void:
	var wrapper := Node3D.new()
	root.add_child(wrapper)
	var skel := Skeleton3D.new()
	skel.name = "Skeleton3D"
	wrapper.add_child(skel)
	var b0 := skel.add_bone("b0")
	var q_rest := Quaternion(Vector3.UP, deg_to_rad(30.0))
	skel.set_bone_rest(b0, Transform3D(Basis(q_rest), Vector3.ZERO))
	skel.reset_bone_poses()

	print("Initial pose rotation (after reset_bone_poses): ", skel.get_bone_pose_rotation(b0))
	print("Initial bone pose transform: ", skel.get_bone_pose(b0))

	# Now create an AnimationPlayer on wrapper
	var anim_player := AnimationPlayer.new()
	wrapper.add_child(anim_player)
	var anim := Animation.new()
	anim.length = 1.0
	var t := anim.add_track(Animation.TYPE_ROTATION_3D)
	anim.track_set_path(t, NodePath("Skeleton3D:b0"))
	# Insert identity rotation
	anim.rotation_track_insert_key(t, 0.0, Quaternion.IDENTITY)

	var lib := AnimationLibrary.new()
	lib.add_animation("test", anim)
	anim_player.add_animation_library("lib", lib)

	anim_player.play("lib/test")
	anim_player.advance(0.0)

	print("After playing animation with key = Quaternion.IDENTITY:")
	print("  bone_pose_rotation: ", skel.get_bone_pose_rotation(b0))
	print("  get_bone_pose: ", skel.get_bone_pose(b0))
	print("  get_bone_global_pose: ", skel.get_bone_global_pose(b0))

	# Now insert key with 45 deg rotation
	var q_45 := Quaternion(Vector3.UP, deg_to_rad(45.0))
	anim.track_set_key_value(t, 0, q_45)
	anim_player.stop()
	anim_player.play("lib/test")
	anim_player.advance(0.0)

	print("After playing animation with key = 45 deg:")
	print("  bone_pose_rotation: ", skel.get_bone_pose_rotation(b0))
	print("  get_bone_pose basis rotation: ", skel.get_bone_pose(b0).basis.get_rotation_quaternion())
	print("  is get_bone_pose equal to Rest * Key? ", skel.get_bone_pose(b0).basis.is_equal_approx(Basis(q_rest * q_45)))
	print("  is get_bone_pose equal to Key? ", skel.get_bone_pose(b0).basis.is_equal_approx(Basis(q_45)))

	quit(0)
