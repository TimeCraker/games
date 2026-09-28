extends SceneTree

func _initialize() -> void:
	var res = load("res://models/aster/aster_character.glb")
	if res == null:
		print("Failed to load aster_character.glb")
		quit(1)
		return
	var scn = res.instantiate()
	get_root().add_child(scn)
	_scan_node(scn)
	quit(0)

func _scan_node(node: Node) -> void:
	if node is MeshInstance3D:
		var mi: MeshInstance3D = node
		print("Mesh: ", mi.name, " surfaces: ", mi.mesh.get_surface_count())
		for i in mi.mesh.get_surface_count():
			var mat = mi.get_active_material(i)
			if mat is BaseMaterial3D:
				print("  surface ", i, " BaseMaterial3D albedo_texture: ", mat.albedo_texture)
			elif mat is ShaderMaterial:
				print("  surface ", i, " ShaderMaterial albedo_texture: ", mat.get_shader_parameter("albedo_texture"))
			else:
				print("  surface ", i, " material: ", mat)
	for child in node.get_children():
		_scan_node(child)
