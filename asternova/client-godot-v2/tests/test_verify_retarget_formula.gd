extends SceneTree

func _initialize() -> void:
	var ps: PackedScene = load("res://scenes/entities/character_aster.tscn")
	var aster = ps.instantiate()
	var skel: Skeleton3D = aster.find_child("Skeleton3D", true, false)
	
	# 测试骨骼: L_Upperarm
	var idx := skel.find_bone("L_Upperarm")
	var p_idx := skel.get_bone_parent(idx)
	
	var rest_g := skel.get_bone_global_rest(idx).basis.get_rotation_quaternion()
	var p_rest_g := skel.get_bone_global_rest(p_idx).basis.get_rotation_quaternion()
	
	# 公式: 目标全局姿态 dst_g = rest_g (假设当前是 rest)
	# 局部旋转: q_local = p_rest_g.inverse() * rest_g
	var q_local := p_rest_g.inverse() * rest_g
	
	# 验证: q_local 是否等于 get_bone_rest(idx) 的 basis quat?
	var rest_local := skel.get_bone_rest(idx).basis.get_rotation_quaternion()
	
	var dot := absf(q_local.dot(rest_local))
	print("--- Mathematical Identity Test ---")
	print("q_local = p_rest_g^-1 * rest_g: ", q_local)
	print("rest_local from skel: ", rest_local)
	print("Dot product: ", dot, " (1.0 means EXACT MATCH)")
	
	# 那么如果用 AnimationPlayer 播放这个 q_local:
	skel.set_bone_pose_rotation(idx, q_local)
	skel.force_update_bone_child_transform(idx)
	var current_g := skel.get_bone_global_pose(idx).basis.get_rotation_quaternion()
	var dot_g := absf(current_g.dot(rest_g))
	print("Resulting global pose dot with rest_g: ", dot_g)
	
	quit(0)
