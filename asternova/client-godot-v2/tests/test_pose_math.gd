extends SceneTree

func _initialize() -> void:
	var skel := Skeleton3D.new()
	var b_parent := skel.add_bone("parent")
	var b_child := skel.add_bone("child")
	skel.set_bone_parent(b_child, b_parent)

	var rot_parent := Basis(Vector3.UP, PI / 2.0)
	var rot_child := Basis(Vector3.RIGHT, PI / 2.0)

	skel.set_bone_rest(b_parent, Transform3D(rot_parent, Vector3(0, 1, 0)))
	skel.set_bone_rest(b_child, Transform3D(rot_child, Vector3(0, 0, 1)))
	skel.reset_bone_poses()

	# 自行根据 pose 层级累乘全局姿态
	var g_parent = skel.get_bone_pose(b_parent)
	var g_child = g_parent * skel.get_bone_pose(b_child)
	print("Calculated global pose before change:")
	print("  parent: ", g_parent.basis)
	print("  child: ", g_child.basis)

	skel.set_bone_pose_rotation(b_child, Quaternion.IDENTITY)
	var g_child_after = g_parent * skel.get_bone_pose(b_child)
	print("Calculated global pose after child set to IDENTITY:")
	print("  child: ", g_child_after.basis)

	quit(0)
