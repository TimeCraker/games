extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(10):
		await process_frame
		
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	var skel: Skeleton3D = rig.skeleton
	
	# Find Aster_Body
	var body_mi: MeshInstance3D = null
	var stack = [rig]
	while stack.size() > 0:
		var curr = stack.pop_back()
		if curr is MeshInstance3D and "Aster_Body" in curr.name:
			body_mi = curr
			break
		for child in curr.get_children():
			stack.push_back(child)
			
	if not body_mi:
		print("Aster_Body not found!")
		quit()
		return
		
	print("Aster_Body found, computing skinned vertex positions...")
	var m = body_mi.mesh
	var arrays = m.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var bones: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
	var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
	
	var bone_count = skel.get_bone_count()
	# Compute skinning matrices: M_b = skel.global_transform * pose_global * bind_inverse
	# Note: In Godot Skeleton3D:
	# bone_global_pose is the pose in skeleton local space.
	# The bind pose is get_bone_rest() accumulated, or bone rest.
	var bone_transforms: Array[Transform3D] = []
	for b in range(bone_count):
		# Skinned vertex transform:
		# Global pose of bone b:
		var gpose = skel.get_bone_global_pose(b)
		var grest = skel.get_bone_global_rest(b)
		var skin_xform = gpose * grest.affine_inverse()
		bone_transforms.append(skin_xform)
		
	var min_skinned = Vector3(999, 999, 999)
	var max_skinned = Vector3(-999, -999, -999)
	var third_leg_verts = []
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
		min_skinned = min_skinned.min(world_v)
		max_skinned = max_skinned.max(world_v)
		
		# Look for vertices near the ground (world_v.y < 0.1) that are NOT feet
		# (e.g. rest.y > 0.4)
		if world_v.y < 0.15 and v.y > 0.4:
			var bone_info = []
			for j in range(4):
				var b_idx = bones[b_idx_base + j]
				var w = weights[b_idx_base + j]
				if w > 0.01:
					bone_info.append("%s(%.2f)" % [skel.get_bone_name(b_idx), w])
			third_leg_verts.append({
				"vi": vi,
				"rest": v,
				"world": world_v,
				"bones": bone_info
			})
			
	print("Skinned bounds min=%s max=%s" % [min_skinned, max_skinned])
	print("Found %d vertices with rest.y > 0.4 and world.y < 0.15:" % third_leg_verts.size())
	for item in third_leg_verts.slice(0, 30):
		print("  v[%d] rest=%s world=%s bones=%s" % [item.vi, item.rest, item.world, item.bones])
		
	quit()
