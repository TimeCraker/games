extends SceneTree

## 颜色/自定义数组探针：确认 Hair_Mask 落在哪个数组通道

func _initialize() -> void:
	var ps: PackedScene = load("res://models/aster/aster_assembled.glb")
	var scene := ps.instantiate()
	root.add_child(scene)
	await physics_frame
	var mi := scene.find_child("Aster_Body", true, false) as MeshInstance3D
	var m := mi.mesh
	for s in m.get_surface_count():
		var arr := m.surface_get_arrays(s)
		var col: Variant = arr[Mesh.ARRAY_COLOR]
		var custom: Variant = arr[Mesh.ARRAY_CUSTOM0]
		var uv2: Variant = arr[Mesh.ARRAY_TEX_UV2]
		var n_v := (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
		print("surface %d: verts=%d color=%s custom0=%s uv2=%s" % [s, n_v,
			col.get("size") if col == null else col.size(),
			custom.size() if custom != null else -1,
			uv2.size() if uv2 != null else -1])
		if col is PackedColorArray and col.size() > 0:
			var red := 0
			var black := 0
			for i in col.size():
				if col[i].r > 0.5:
					red += 1
				elif col[i].r < 0.05 and col[i].g < 0.05:
					black += 1
			print("  color: red=%d black=%d sample0=%s sample1=%s" % [red, black, col[0], col[1]])
		if custom.size() > 0:
			print("  custom0 flags? first bytes: %d %d %d %d" % [custom[0], custom[1], custom[2], custom[3]])
	print("PROBE_DONE")
	quit(0)
