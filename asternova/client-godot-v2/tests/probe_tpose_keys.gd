extends SceneTree
func _initialize() -> void:
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	var a: Animation = lib.get_animation("TPose")
	print("TPose len=%.3f tracks=%d" % [a.length, a.get_track_count()])
	for t in a.get_track_count():
		var p := a.track_get_path(t)
		var bone := String(p.get_subname(0))
		if bone in ["Root", "Hip", "L_Upperarm", "R_Upperarm"] and a.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			var n := a.track_get_key_count(t)
			var q0: Quaternion = a.rotation_track_interpolate(t, 0.0)
			print("  %s rot keys=%d q0=%s" % [bone, n, str(q0)])
	# 运行时 FK：Root 全局姿态
	var glb: PackedScene = load("res://models/aster/aster_assembled.glb")
	var holder: Node3D = Node3D.new()
	root.add_child(holder)
	var inst: Node = glb.instantiate()
	holder.add_child(inst)
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	var player := AnimationPlayer.new()
	holder.add_child(player)
	player.root_node = player.get_path_to(inst)  # 指向 glb 根，轨道 Skeleton3D:X 从其子解析
	player.add_animation_library("x", lib)
	player.play("x/TPose")
	player.advance(0.0)
	var ri := skel.find_bone("Root")
	print("Root global pose rot=", str(skel.get_bone_global_pose(ri).basis.get_rotation_quaternion()))
	var ui := skel.find_bone("L_Upperarm")
	print("L_Upperarm global dir=", str((skel.get_bone_global_pose(skel.get_bone_children(ui)[0]).origin - skel.get_bone_global_pose(ui).origin).normalized().snapped(Vector3(0.01,0.01,0.01))))
	quit(0)
