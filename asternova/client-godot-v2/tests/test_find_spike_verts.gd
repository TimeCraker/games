extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(5):
		await process_frame
		
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	var skel: Skeleton3D = rig.skeleton
	var body_mi: MeshInstance3D = rig.find_child("Aster_Body", true, false)
	
	var m = body_mi.mesh
	var arrays = m.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var bones: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
	var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
	var bone_count = skel.get_bone_count()
	
	var bone_transforms: Array[Transform3D] = []
	for b in range(bone_count):
		var gpose = skel.get_bone_global_pose(b)
		var grest = skel.get_bone_global_rest(b)
		bone_transforms.append(gpose * grest.affine_inverse())
		
	var spike_verts = []
	for vi in range(verts.size()):
		var v = verts[vi]
		var skinned_v = Vector3.ZERO
		var b_idx_base = vi * 4
		for j in range(4):
			var b_idx = bones[b_idx_base + j]
			var w = weights[b_idx_base + j]
			if w > 0.0 and b_idx >= 0 and b_idx < bone_count:
				skinned_v += (bone_transforms[b_idx] * v) * w
		var world_v = skel.global_transform * skinned_v
		
		# Spikes shoot up into the air: Y > 1.8 or abs(X) > 0.8
		if world_v.y > 1.85 or abs(world_v.x) > 0.8:
			var binfo = []
			for j in range(4):
				var b_idx = bones[b_idx_base + j]
				var w = weights[b_idx_base + j]
				if w > 0.01:
					binfo.append("%s(%.2f)" % [skel.get_bone_name(b_idx), w])
			spike_verts.append({"vi": vi, "rest": v, "world": world_v, "bones": binfo})
			
	print("Found %d spike vertices:" % spike_verts.size())
	for s in spike_verts.slice(0, 20):
		print("  v[%d] rest=%s world=%s bones=%s" % [s.vi, s.rest, s.world, s.bones])
	quit()
