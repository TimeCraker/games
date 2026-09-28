extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	for bname in ["Hip", "L_Thigh", "L_Calf", "L_Foot", "L_CalfTwist01"]:
		var idx := skel.find_bone(bname)
		print(bname, ": index=", idx, " global_origin=", skel.get_bone_global_pose(idx).origin, " rest_origin=", skel.get_bone_rest(idx).origin)
	quit(0)
