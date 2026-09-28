extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://scenes/entities/character_aster.tscn")
	var inst: AsterRig = scene.instantiate()
	root.add_child(inst)
	# Wait one frame for _ready
	print("Instantiated AsterRig!")
	var mi: MeshInstance3D = inst.skeleton.get_node_or_null("Aster_Body") as MeshInstance3D
	if mi == null:
		print("Aster_Body is NULL!")
		quit(1)
		return
	print("Aster_Body surfaces: ", mi.mesh.get_surface_count())
	var mat := mi.get_surface_override_material(0)
	print("Surface 0 override mat: ", mat)
	if mat is ShaderMaterial:
		var tex = mat.get_shader_parameter("albedo_texture")
		print("albedo_texture: ", tex)
		if tex is Texture2D:
			print("Texture size: ", tex.get_size(), " format: ", tex.get_image().get_format())
			var img = tex.get_image()
			print("Sample pixel (100,100): ", img.get_pixel(100, 100))
			print("Sample pixel (1000,1000): ", img.get_pixel(1000, 1000))
	quit(0)
