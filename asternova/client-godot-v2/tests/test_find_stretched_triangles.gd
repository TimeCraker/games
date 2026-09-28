extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(5):
		await process_frame
		
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	var skel: Skeleton3D = rig.skeleton
	var body_mi: MeshInstance3D = rig.find_child("Aster_Body", true, false)
	var skin: Skin = body_mi.skin
	
	for i in range(15):
		await physics_frame
		
	# Build skinning transform for each skin bind
	var skin_transforms: Array[Transform3D] = []
	for b in range(skin.get_bind_count()):
		var bname = skin.get_bind_name(b)
		var skel_idx = skel.find_bone(bname)
		if skel_idx >= 0:
			var gpose = skel.get_bone_global_pose(skel_idx)
			var grest = skel.get_bone_global_rest(skel_idx)
			skin_transforms.append(gpose * grest.affine_inverse())
		else:
			skin_transforms.append(Transform3D.IDENTITY)
			
	var m = body_mi.mesh
	var arrays = m.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	var bones: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
	var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
	
	print("Total verts:", verts.size(), "Total indices:", indices.size(), "Triangles:", indices.size() / 3)
	
	# Compute skinned positions
	var skinned_verts: PackedVector3Array = PackedVector3Array()
	skinned_verts.resize(verts.size())
	for vi in range(verts.size()):
		var v = verts[vi]
		var sv = Vector3.ZERO
		var base = vi * 4
		for j in range(4):
			var s_idx = bones[base + j]
			var w = weights[base + j]
			if w > 0.0 and s_idx >= 0 and s_idx < skin_transforms.size():
				sv += (skin_transforms[s_idx] * v) * w
		skinned_verts[vi] = skel.global_transform * sv
		
	# Check triangle edge lengths
	var huge_tris = []
	for ti in range(indices.size() / 3):
		var i0 = indices[ti * 3 + 0]
		var i1 = indices[ti * 3 + 1]
		var i2 = indices[ti * 3 + 2]
		var p0 = skinned_verts[i0]
		var p1 = skinned_verts[i1]
		var p2 = skinned_verts[i2]
		var d01 = p0.distance_to(p1)
		var d12 = p1.distance_to(p2)
		var d20 = p2.distance_to(p0)
		var max_edge = max(d01, max(d12, d20))
		if max_edge > 0.35:
			huge_tris.append({
				"ti": ti,
				"indices": [i0, i1, i2],
				"max_edge": max_edge,
				"p0": p0, "p1": p1, "p2": p2,
				"b0": skin.get_bind_name(bones[i0*4]),
				"b1": skin.get_bind_name(bones[i1*4]),
				"b2": skin.get_bind_name(bones[i2*4]),
			})
			
	print("Found %d huge triangles (>0.35m edge):" % huge_tris.size())
	for ht in huge_tris.slice(0, 20):
		print("  Tri %d max_edge=%.2fm: bones=[%s, %s, %s] p0=%s p1=%s p2=%s" % [
			ht.ti, ht.max_edge, ht.b0, ht.b1, ht.b2, ht.p0, ht.p1, ht.p2
		])
	quit()
