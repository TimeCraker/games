extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	
	for bname in ["Hip", "L_Thigh", "L_Calf", "L_Foot", "L_CalfTwist01"]:
		var idx := skel.find_bone(bname)
		var gpose := skel.get_bone_global_pose(idx)
		print(bname, ": global_origin=", gpose.origin, " rest_origin=", skel.get_bone_rest(idx).origin)
		var children = skel.get_bone_children(idx)
		print("  children:", [children.map(func(c): return skel.get_bone_name(c))])
	
	var calf_idx := skel.find_bone("L_Calf")
	var children = skel.get_bone_children(calf_idx)
	for c in children:
		var c_name = skel.get_bone_name(c)
		var vec = skel.get_bone_global_pose(c).origin - skel.get_bone_global_pose(calf_idx).origin
		print("Vector from L_Calf to ", c_name, ": ", vec, " normalized: ", vec.normalized())
	quit(0)
