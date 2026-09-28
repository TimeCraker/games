extends SceneTree

func _initialize() -> void:
	var path := "res://models/aster/aster_character.glb"
	var packed: PackedScene = load(path)
	if not packed:
		print("加载失败!")
		quit(1)
		return
	var root := packed.instantiate()
	print("--- 重新导入后的 aster_character.glb 节点树 ---")
	_dump(root, 0)
	quit(0)

func _dump(node: Node, depth: int) -> void:
	var pad := "  ".repeat(depth)
	print(pad, node.name, " (", node.get_class(), ")")
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		if mi.mesh:
			print(pad, "  [Mesh] surfaces=", mi.mesh.get_surface_count())
			for s in mi.mesh.get_surface_count():
				var arr = mi.mesh.surface_get_arrays(s)
				var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
				print(pad, "    surface ", s, ": verts=", verts.size())
	if node is Skeleton3D:
		var sk := node as Skeleton3D
		print(pad, "  [Skeleton3D] bones=", sk.get_bone_count())
		for b in mini(10, sk.get_bone_count()):
			print(pad, "    bone ", b, ": ", sk.get_bone_name(b))
	if node is AnimationPlayer:
		var ap := node as AnimationPlayer
		print(pad, "  [AnimationPlayer] anims=", ap.get_animation_list())
	for c in node.get_children():
		_dump(c, depth + 1)
