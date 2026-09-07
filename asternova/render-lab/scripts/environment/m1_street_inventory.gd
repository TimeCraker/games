extends SceneTree
## M1 street sandbox world-space inventory (无头标定诊断, 不随游戏发布).
## 1) 遍历总装场景全部 MeshInstance3D, 输出世界坐标 AABB (道具贴墙/贴花布点的标定底座);
## 2) 物理射线网格采样地面高度场 (坡道 15 度纵坡, 道具落地必须逐点贴地);
## 3) 输出 StaticBody3D 碰撞盒世界 AABB (便利店侧墙外立面坐标).

const SCENE := "res://scenes/levels/m1_endfield_street.tscn"
const GRID_X_FROM := -26.0
const GRID_X_TO := 14.0
const GRID_Z_FROM := 32.0
const GRID_Z_TO := -50.0
const GRID_STEP := 2.0


func _initialize() -> void:
	_run()


func _run() -> void:
	var ps: PackedScene = load(SCENE)
	if ps == null:
		push_error("cannot load " + SCENE)
		quit(1)
		return
	var scene := ps.instantiate()
	root.add_child(scene)
	for i in 8:
		await physics_frame

	print("=== MESH AABB DUMP (name | center | size | min | max) ===")
	_dump_meshes(scene, scene)

	print("=== STATICBODY COLLISION DUMP ===")
	_dump_collisions(scene)

	print("=== GROUND HEIGHT GRID (rows=z, cols=x, value=ground_y) ===")
	var space := root.world_3d.direct_space_state
	var header := "z\\x   "
	var x := GRID_X_FROM
	while x <= GRID_X_TO:
		header += "%6.0f" % x
		x += GRID_STEP
	print(header)
	var z := GRID_Z_FROM
	while z >= GRID_Z_TO:
		var row := "%5.0f " % z
		x = GRID_X_FROM
		while x <= GRID_X_TO:
			var q := PhysicsRayQueryParameters3D.create(
					Vector3(x, 50.0, z), Vector3(x, -10.0, z))
			q.collision_mask = 1
			var hit := space.intersect_ray(q)
			row += " HOLE  " if hit.is_empty() else "%6.2f" % hit.position.y
			x += GRID_STEP
		print(row)
		z -= GRID_STEP
	quit(0)


func _dump_meshes(node: Node, scene: Node) -> void:
	for child in node.get_children():
		if child is MeshInstance3D and child.visible:
			var mi := child as MeshInstance3D
			var aabb := mi.mesh.get_aabb()
			var xf := mi.global_transform
			var mn := Vector3(INF, INF, INF)
			var mx := -mn
			for i in 8:
				var corner := xf * (aabb.position + Vector3(
						aabb.size.x * float(i & 1), aabb.size.y * float((i >> 1) & 1),
						aabb.size.z * float((i >> 2) & 1)))
				mn = mn.min(corner)
				mx = mx.max(corner)
			var rel := scene.get_path_to(mi)
			print("%s | c=%s | s=%s | mn=%s | mx=%s" % [rel, (mn + mx) * 0.5,
					mx - mn, mn, mx])
		_dump_meshes(child, scene)


func _dump_collisions(node: Node) -> void:
	for child in node.get_children():
		if child is CollisionShape3D and child.shape is BoxShape3D:
			var cs := child as CollisionShape3D
			var box := cs.shape as BoxShape3D
			var xf := cs.global_transform
			var mn := Vector3(INF, INF, INF)
			var mx := -mn
			for i in 8:
				var corner := xf * (cs.position + Vector3(
						box.size.x * float(i & 1), box.size.y * float((i >> 1) & 1),
						box.size.z * float((i >> 2) & 1)))
				mn = mn.min(corner)
				mx = mx.max(corner)
			print("%s | mn=%s | mx=%s" % [cs.name, mn, mx])
		_dump_collisions(child)
