extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(5):
		await process_frame
		
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	var skel: Skeleton3D = rig.skeleton
	print("Skeleton bone count:", skel.get_bone_count())
	
	# Find all meshes under rig
	var meshes = []
	var stack = [rig]
	while stack.size() > 0:
		var curr = stack.pop_back()
		if curr is MeshInstance3D:
			meshes.append(curr)
		for child in curr.get_children():
			stack.push_back(child)
			
	print("Total meshes found:", meshes.size())
	for mi in meshes:
		print("Mesh name:", mi.name, "visible:", mi.visible, "parent:", mi.get_parent().name)
		var m = mi.mesh
		if m is ArrayMesh:
			var arrays = m.surface_get_arrays(0)
			var verts = arrays[Mesh.ARRAY_VERTEX]
			var bones = arrays[Mesh.ARRAY_BONES] if arrays.size() > Mesh.ARRAY_BONES else null
			var weights = arrays[Mesh.ARRAY_WEIGHTS] if arrays.size() > Mesh.ARRAY_WEIGHTS else null
			print("  surface 0 verts:", verts.size())
			# Check global positions of skin
			var low_verts = []
			for vi in range(verts.size()):
				# In rest or bind pose
				var v = verts[vi]
				# Check global pos via skeleton if bones exist
				if v.y < 0.2 and abs(v.x) < 0.1:
					low_verts.append(vi)
			print("  verts with bind y < 0.2, abs(x) < 0.1:", low_verts.size())
			
	for mi in meshes:
		var aabb: AABB = mi.global_transform * mi.get_aabb()
		print("Mesh: %-20s | Visible: %-5s | Global AABB: %s | Global Pos: %s" % [
			mi.name, mi.visible, aabb, mi.global_position
		])

	# Now let's check bone pose positions in skeleton!
	print("\n=== Skeleton Bone Rest vs Pose Transforms ===")
	for bi in range(skel.get_bone_count()):
		var bname = skel.get_bone_name(bi)
		var rest_rot = skel.get_bone_rest(bi).basis.get_euler()
		var pose_rot = skel.get_bone_pose_rotation(bi).get_euler()
		var pose_pos = skel.get_bone_pose_position(bi)
		var bname_low = bname.to_lower()
		if "spine" in bname_low or "hips" in bname_low or "leg" in bname_low or "thigh" in bname_low or "shin" in bname_low or "socket" in bname_low:
			print("Bone [%2d] %-25s: pose_pos=%s, pose_rot_deg=(%.1f, %.1f, %.1f), rest_rot_deg=(%.1f, %.1f, %.1f)" % [
				bi, bname, pose_pos,
				rad_to_deg(pose_rot.x), rad_to_deg(pose_rot.y), rad_to_deg(pose_rot.z),
				rad_to_deg(rest_rot.x), rad_to_deg(rest_rot.y), rad_to_deg(rest_rot.z)
			])
			
	quit()
