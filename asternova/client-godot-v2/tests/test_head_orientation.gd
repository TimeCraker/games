@tool
extends SceneTree

func _init() -> void:
	var packed = load("res://models/aster/aster_character.glb")
	var scene = packed.instantiate()
	var body: MeshInstance3D = scene.find_child("Aster_Body", true, false)
	var arrays = body.mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var norms: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
	
	var head_indices = []
	for i in range(verts.size()):
		if verts[i].y > 1.35 and abs(verts[i].x) < 0.05:
			head_indices.append(i)
	
	print("Found head center verts in Godot: ", head_indices.size())
	var sum_n = Vector3.ZERO
	var min_pos = Vector3(999, 999, 999)
	var max_pos = Vector3(-999, -999, -999)
	for idx in head_indices:
		sum_n += norms[idx]
		min_pos = min_pos.min(verts[idx])
		max_pos = max_pos.max(verts[idx])
	var avg_n = sum_n / head_indices.size() if head_indices.size() > 0 else Vector3.ZERO
	print("Godot Head avg normal: ", avg_n)
	print("Godot Head X span: [", min_pos.x, ", ", max_pos.x, "]")
	print("Godot Head Y span: [", min_pos.y, ", ", max_pos.y, "]")
	print("Godot Head Z span: [", min_pos.z, ", ", max_pos.z, "]")
	quit(0)
