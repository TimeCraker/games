extends SceneTree

func _initialize() -> void:
	var skel_scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = skel_scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]

	var l_idx := skel.find_bone("L_Upperarm")
	var l_gt := skel.get_bone_global_rest(l_idx)
	var q_l := Quaternion(l_gt.basis.y, Vector3(-1, 0, 0))
	var res_l := q_l * l_gt.basis.y
	print("Left arm auto-aligned dir: ", res_l)

	var r_idx := skel.find_bone("R_Upperarm")
	var r_gt := skel.get_bone_global_rest(r_idx)
	var q_r := Quaternion(r_gt.basis.y, Vector3(1, 0, 0))
	var res_r := q_r * r_gt.basis.y
	print("Right arm auto-aligned dir: ", res_r)

	quit(0)
