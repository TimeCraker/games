extends SceneTree

## 资产真值探针（无头）：刀身/刀鞘网格 AABB（节点空间）、双插槽 BoneAttachment 变换、
## 刀身 authored 变换、握心世界坐标 vs 掌心世界坐标。定位挂载数学的最后真相。
##   godot --headless --path client-godot-v2 -s tests/probe_asset_v52.gd

func _initialize() -> void:
	var ps: PackedScene = load("res://models/aster/aster_assembled.glb")
	if ps == null:
		printerr("FATAL: GLB 载入失败")
		quit(1)
		return
	var scene := ps.instantiate()
	root.add_child(scene)
	await physics_frame
	await physics_frame

	var skel := scene.find_child("Skeleton3D", true, false) as Skeleton3D
	print("skeleton=", skel, " bones=", skel.get_bone_count() if skel else -1)
	if skel == null:
		quit(1)
		return

	for bn in ["Hand_R_Weapon_Socket", "Pelvis_L_Scabbard_Socket", "R_Hand", "Hip"]:
		var idx := skel.find_bone(bn)
		if idx < 0:
			print("bone %s: MISSING" % bn)
			continue
		var pose := skel.get_bone_global_pose(idx)
		print("bone %s: idx=%d origin=%s basis_z=%s basis_y=%s" % [
			bn, idx, pose.origin, (pose.basis.z).snappedf(0.001), (pose.basis.y).snappedf(0.001)])

	var blade := scene.find_child("Katana_Blade", true, false) as MeshInstance3D
	var scab := scene.find_child("Katana_Scabbard", true, false) as MeshInstance3D
	for mi: MeshInstance3D in [blade, scab]:
		if mi == null:
			print("MISSING mesh node")
			continue
		var aabb := mi.mesh.get_aabb()
		print("%s: parent=%s transform=%s" % [mi.name, mi.get_parent().name, mi.transform])
		print("  mesh_aabb pos=%s size=%s" % [aabb.position, aabb.size])
		print("  global_pos=%s" % mi.global_position)

	# 握心/掌心几何（蒙皮 rest 状态下）
	if blade:
		var hand_idx := skel.find_bone("Hand_R_Weapon_Socket")
		var rhand_idx := skel.find_bone("R_Hand")
		var socket_pose := skel.global_transform * skel.get_bone_global_pose(hand_idx)
		var rh_pose := skel.global_transform * skel.get_bone_global_pose(rhand_idx)
		# 掌心 = R_Hand 骨原点沿骨轴前移半掌（Socket 骨即标定在半掌处：实测偏移 0.0812）
		var palm: Vector3 = rh_pose * Vector3(0, 0.0812, 0)
		var grip_local := Vector3(0, 0.13, 0)
		var grip_node: Vector3 = blade.global_transform * grip_local
		print("GRIP blade_basis_y=%s basis_z=%s" % [
			blade.global_transform.basis.y.snappedf(0.001),
			blade.global_transform.basis.z.snappedf(0.001)])
		print("GRIP grip_world=%s socket_origin=%s palm=%s" % [
			grip_node, socket_pose.origin, palm])
		print("GRIP dist(grip,socket)=%.4f dist(grip,palm)=%.4f" % [
			grip_node.distance_to(socket_pose.origin), grip_node.distance_to(palm)])
		# 修正量推导：要握心落回插槽原点，刀身节点原点应为 -basis*(0,0.13,0)
		var fix_origin: Vector3 = blade.global_transform.basis * Vector3(0, -0.13, 0)
		print("GRIP required_node_origin(bone space)=%s" % fix_origin.snappedf(0.0001))
	print("PROBE_DONE")
	quit(0)
