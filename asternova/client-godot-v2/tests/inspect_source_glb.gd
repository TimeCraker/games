extends SceneTree

func _initialize() -> void:
	var glb_path := "c:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/models/source/aster_tripo_39caf44b/aster_source.glb"
	var gltf := GLTFDocument.new()
	var state := GLTFState.new()
	var err := gltf.append_from_file(glb_path, state)
	if err != OK:
		print("加载失败: ", err)
		quit(1)
		return
	var root := gltf.generate_scene(state)
	print("--- 原厂 aster_source.glb 根节点: ", root.name, " ---")
	_dump_nodes(root, 0)
	quit(0)

func _dump_nodes(node: Node, depth: int) -> void:
	var pad := "  ".repeat(depth)
	print(pad, node.name, " (", node.get_class(), ")")
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		if mi.mesh:
			print(pad, "  [Mesh] surfaces=", mi.mesh.get_surface_count())
			for s in mi.mesh.get_surface_count():
				var arr = mi.mesh.surface_get_arrays(s)
				var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
				var mat = mi.get_active_material(s)
				print(pad, "    surface ", s, ": verts=", verts.size(), " mat=", mat.resource_name if mat else "null")
	if node is Skeleton3D:
		var sk := node as Skeleton3D
		print(pad, "  [Skeleton3D] bones=", sk.get_bone_count())
		for b in mini(10, sk.get_bone_count()):
			print(pad, "    bone ", b, ": ", sk.get_bone_name(b))
	if node is AnimationPlayer:
		var ap := node as AnimationPlayer
		print(pad, "  [AnimationPlayer] anims=", ap.get_animation_list())
	for c in node.get_children():
		_dump_nodes(c, depth + 1)
