extends SceneTree

func _init() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst := scene.instantiate()
	var body: MeshInstance3D = inst.find_child("Aster_Body", true, false)
	var mat = body.get_active_material(0)
	print("Body material type: ", mat.get_class())
	if mat is BaseMaterial3D:
		print("  albedo_color: ", mat.albedo_color)
		print("  albedo_texture: ", mat.albedo_texture)
		print("  roughness: ", mat.roughness)
		print("  metallic: ", mat.metallic)
		print("  emission_enabled: ", mat.emission_enabled)
		print("  shading_mode: ", mat.shading_mode)
		if mat.albedo_texture:
			print("  texture size: ", mat.albedo_texture.get_size())
	quit(0)
