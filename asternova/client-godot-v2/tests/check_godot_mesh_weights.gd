extends SceneTree

func _initialize() -> void:
	var scn: Node = load("res://models/aster/aster_character.glb").instantiate()
	var mesh_inst: MeshInstance3D = scn.find_child("Aster_Body", true, false)
	var mesh: ArrayMesh = mesh_inst.mesh
	var arrays := mesh.surface_get_arrays(0)
	var bones: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
	var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var skel: Skeleton3D = scn.find_child("Skeleton3D", true, false)
	
	print("Surface 0 vert count: ", verts.size(), " bones size: ", bones.size())
	# 检查在 Z 位于腰部（Godot Y在 0.8-1.0）且靠近右侧（X > 0.1）的顶点
	var r_forearm_idx := skel.find_bone("R_Forearm")
	var r_upper_idx := skel.find_bone("R_Upperarm")
	print("R_Forearm bone idx: ", r_forearm_idx, " R_Upperarm idx: ", r_upper_idx)
	
	var corrupt := 0
	for vi in range(verts.size()):
		var v := verts[vi]
		if v.y > 0.75 and v.y < 1.05 and abs(v.x) < 0.25:
			# 检查是否有 R_Forearm 权重
			for b in range(4):
				var bidx := bones[vi * 4 + b]
				var w := weights[vi * 4 + b]
				if (bidx == r_forearm_idx or bidx == r_upper_idx) and w > 0.05:
					corrupt += 1
					if corrupt <= 10:
						print("Corrupt vert in Godot: vi=", vi, " pos=", v, " bone=", skel.get_bone_name(bidx), " w=", w)
	print("Total corrupt trunk verts with arm weights in Godot: ", corrupt)
	quit(0)
