@tool
extends SceneTree

func _init() -> void:
	var packed = load("res://models/aster/aster_character.glb")
	if not packed:
		print("Failed to load aster_character.glb")
		quit(1)
		return
	var scene = packed.instantiate()
	print("Scene root: ", scene.name, " (", scene.get_class(), ")")
	_print_tree(scene, "  ")
	quit(0)

func _print_tree(node: Node, indent: String) -> void:
	var info = ""
	if node is MeshInstance3D:
		var mi = node as MeshInstance3D
		info = " mesh=" + str(mi.mesh.get_name() if mi.mesh else "null") + " surfaces=" + str(mi.mesh.get_surface_count() if mi.mesh else 0)
		if mi.mesh:
			for s in range(mi.mesh.get_surface_count()):
				var mat = mi.get_active_material(s)
				var mat_name = mat.resource_name if mat else "null"
				var tex_name = "none"
				if mat is BaseMaterial3D and mat.albedo_texture:
					tex_name = mat.albedo_texture.resource_path
				info += " [surf" + str(s) + ": " + mat_name + " tex=" + tex_name + "]"
	elif node is Skeleton3D:
		var skel = node as Skeleton3D
		info = " bones=" + str(skel.get_bone_count())
	print(indent, node.name, " (", node.get_class(), ")", info)
	for child in node.get_children():
		_print_tree(child, indent + "  ")
