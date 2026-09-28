@tool
extends SceneTree

func _init() -> void:
	var packed = load("res://models/aster/aster_character.glb")
	var scene = packed.instantiate()
	var body: MeshInstance3D = scene.find_child("Aster_Body", true, false)
	if body and body.mesh:
		var m = body.mesh
		print("Mesh: ", m.resource_name, " surfaces: ", m.get_surface_count())
		var arrays = m.surface_get_arrays(0)
		var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var uvs: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
		var uvs2: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV2] if arrays.size() > Mesh.ARRAY_TEX_UV2 else PackedVector2Array()
		print("Verts count: ", verts.size())
		print("UV count: ", uvs.size())
		print("UV2 count: ", uvs2.size())
		if uvs.size() > 10:
			print("Sample UVs: ", uvs[0], uvs[1], uvs[2], uvs[3], uvs[4])
		# Check active material on surface 0
		var mat = body.get_active_material(0)
		print("Original active material: ", mat)
		if mat is BaseMaterial3D:
			print("  albedo_color: ", mat.albedo_color)
			print("  albedo_texture: ", mat.albedo_texture)
	quit(0)
