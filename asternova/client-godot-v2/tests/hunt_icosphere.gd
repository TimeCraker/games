extends SceneTree
func _init() -> void:
	for path in ["res://models/aster/aster_character.glb", "res://models/aster/aster_assembled.glb"]:
		var glb: PackedScene = load(path) as PackedScene
		if glb == null:
			print("missing", path)
			continue
		var inst: Node = glb.instantiate()
		root.add_child(inst)
		var stack: Array = [inst]
		while not stack.is_empty():
			var n: Node = stack.pop_back()
			var nm: String = String(n.name).to_lower()
			if nm.contains("ico") or nm.contains("sphere") or nm.contains("debug") or nm.contains("helper") or nm.contains("cube") or nm.contains("cylinder"):
				print("HIT", path, n.name, n.get_class())
			if n is MeshInstance3D:
				var mi: MeshInstance3D = n as MeshInstance3D
				if mi.mesh is SphereMesh or mi.mesh is BoxMesh or mi.mesh is CylinderMesh:
					print("PRIM", path, n.name, mi.mesh.get_class(), "pos", mi.global_position)
			for c in n.get_children():
				stack.push_back(c)
		print("done", path, "children_ok")
	quit()
