@tool
extends SceneTree

func _init() -> void:
	var packed = load("res://models/aster/aster_character.glb")
	var scene = packed.instantiate()
	var body: MeshInstance3D = scene.find_child("Aster_Body", true, false)
	var arrays = body.mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var norms: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
	
	# Find vertex with max and min Z around head (Y in 1.45..1.55)
	var max_z_v = Vector3.ZERO
	var min_z_v = Vector3.ZERO
	var max_z = -999.0
	var min_z = 999.0
	var max_z_n = Vector3.ZERO
	var min_z_n = Vector3.ZERO
	for i in range(verts.size()):
		if verts[i].y > 1.45 and verts[i].y < 1.55 and abs(verts[i].x) < 0.03:
			if verts[i].z > max_z:
				max_z = verts[i].z
				max_z_v = verts[i]
				max_z_n = norms[i]
			if verts[i].z < min_z:
				min_z = verts[i].z
				min_z_v = verts[i]
				min_z_n = norms[i]
	print("Max Z point (face or back?): ", max_z_v, " normal: ", max_z_n)
	print("Min Z point (face or back?): ", min_z_v, " normal: ", min_z_n)
	quit(0)
