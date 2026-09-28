extends SceneTree

func _init() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst := scene.instantiate()
	var body: MeshInstance3D = inst.find_child("Aster_Body", true, false)
	print("Aster_Body surfaces: ", body.mesh.get_surface_count())
	for s in body.mesh.get_surface_count():
		var arrs := body.mesh.surface_get_arrays(s)
		var uv2 = arrs[Mesh.ARRAY_TEX_UV2]
		print("Surface ", s, " ARRAY_TEX_UV2: ", uv2 != null, " type: ", typeof(uv2))
		if uv2 is PackedVector2Array:
			print("  size: ", uv2.size())
			var count_gt_025 := 0
			for i in min(100, uv2.size()):
				if uv2[i].x > 0.25:
					count_gt_025 += 1
			print("  Sample in first 100 with x > 0.25: ", count_gt_025)
	quit(0)
