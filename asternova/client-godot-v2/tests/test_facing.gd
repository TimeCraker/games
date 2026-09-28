@tool
extends SceneTree

func _init() -> void:
	var player = load("res://scenes/entities/player.tscn").instantiate() as PlayerController
	root.add_child(player)
	for i in range(5):
		await process_frame
		
	player.input_direction = Vector3(0, 0, -1)
	player.align_visual_rotation(1.0)
	
	var rig = player.visual_root.get_node("CharacterAster")
	var skel: Skeleton3D = rig.find_child("Skeleton3D", true, false)
	var head_idx = skel.find_bone("Head")
	var head_pose = skel.global_transform * skel.get_bone_global_pose(head_idx)
	print("When input_direction is (0, 0, -1) [running away from camera]:")
	print("  visual_root rotation: ", player.visual_root.rotation)
	print("  Head pose basis Z: ", head_pose.basis.z)
	print("  Head pose basis Y: ", head_pose.basis.y)
	
	# Check where nose points
	var body: MeshInstance3D = rig.find_child("Aster_Body", true, false)
	var arrays = body.mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var norms: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
	var max_z_idx = -1
	var max_z = -999.0
	for i in range(verts.size()):
		if verts[i].y > 1.45 and verts[i].y < 1.55 and abs(verts[i].x) < 0.03:
			if verts[i].z > max_z:
				max_z = verts[i].z
				max_z_idx = i
	
	var nose_norm_world = body.global_transform.basis * norms[max_z_idx]
	print("  Nose normal in world space: ", nose_norm_world)
	quit(0)
