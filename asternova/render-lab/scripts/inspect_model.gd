extends SceneTree

func _init() -> void:
	var scene: PackedScene = load("res://models/aster/aster_model.glb")
	if not scene:
		print("ERROR: Failed to load aster_base.glb")
		quit(1)
		return
	var inst = scene.instantiate()
	_print_tree(inst, "")
	quit(0)

func _print_tree(node: Node, indent: String) -> void:
	var info: String = indent + node.name + " (" + node.get_class() + ")"
	if node is MeshInstance3D and node.name in ["Face", "Body", "Hair001"]:
		info += " [MeshInstance3D, surfaces=" + str(node.mesh.get_surface_count() if node.mesh else 0) + "]"
		if node.mesh:
			for i in range(node.mesh.get_surface_count()):
				var mat: Material = node.mesh.surface_get_material(i)
				if mat:
					info += "\n" + indent + "    Surface " + str(i) + ": " + mat.resource_name + " [" + mat.get_class() + "]"
					if mat is StandardMaterial3D:
						info += " col=" + str(mat.albedo_color) + " tex=" + (mat.albedo_texture.resource_path if mat.albedo_texture else "null")
					elif mat is ShaderMaterial:
						info += " shader=" + (mat.shader.resource_path if mat.shader else "null")
				else:
					info += "\n" + indent + "    Surface " + str(i) + ": null"
	print(info)
	for child in node.get_children():
		_print_tree(child, indent + "  ")
