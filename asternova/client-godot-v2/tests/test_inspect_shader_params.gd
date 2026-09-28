@tool
extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/character_aster.tscn").instantiate()
	root.add_child(scene)
	for i in range(2):
		await process_frame
	
	var body: MeshInstance3D = scene.find_child("Aster_Body", true, false)
	if body:
		print("Body found!")
		var mat = body.get_surface_override_material(0)
		print("mat is: ", mat)
		if mat is ShaderMaterial:
			print("Shader: ", mat.shader.resource_path)
			var tex = mat.get_shader_parameter("albedo_texture")
			print("  albedo_texture: ", tex)
			if tex is Texture2D:
				print("  albedo_texture path: ", tex.resource_path, " size: ", tex.get_size())
			else:
				print("  albedo_texture is NOT Texture2D! It is: ", typeof(tex))
			print("  albedo_color: ", mat.get_shader_parameter("albedo_color"))
	quit(0)
