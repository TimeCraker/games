extends SceneTree

func _init() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst := scene.instantiate()
	_print_tree(inst, "")
	quit(0)

func _print_tree(node: Node, indent: String) -> void:
	print("%s%s (%s)" % [indent, node.name, node.get_class()])
	if node is MeshInstance3D:
		print("%s  Mesh: %s, surfaces: %d" % [indent, node.mesh.resource_name, node.mesh.get_surface_count()])
		for i in node.mesh.get_surface_count():
			var mat = node.get_active_material(i)
			print("%s  Surface %d mat: %s" % [indent, i, mat])
	for c in node.get_children():
		_print_tree(c, indent + "  ")
