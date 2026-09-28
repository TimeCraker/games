extends SceneTree

func _initialize() -> void:
	var skel_scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = skel_scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]

	# 测试抬起左手臂 45 度
	var l_idx := skel.find_bone("L_Upperarm")
	var l_gt := skel.get_bone_global_rest(l_idx)
	print("L_Upperarm original Y dir (bone vector): ", l_gt.basis.y)

	# 绕 Z 轴旋转 -45° (在 Godot 坐标系中，抬起左手臂)
	var q_lift_l := Quaternion(Vector3.FORWARD, deg_to_rad(-45.0))
	var lifted_basis_l := Basis(q_lift_l) * l_gt.basis
	print("L_Upperarm lifted Y dir: ", lifted_basis_l.y)

	# 绕 Z 轴旋转 +45° (抬起右手臂)
	var r_idx := skel.find_bone("R_Upperarm")
	var r_gt := skel.get_bone_global_rest(r_idx)
	var q_lift_r := Quaternion(Vector3.FORWARD, deg_to_rad(45.0))
	var lifted_basis_r := Basis(q_lift_r) * r_gt.basis
	print("R_Upperarm original Y dir: ", r_gt.basis.y)
	print("R_Upperarm lifted Y dir: ", lifted_basis_r.y)

	quit(0)
