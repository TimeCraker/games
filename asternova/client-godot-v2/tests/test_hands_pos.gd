extends SceneTree

func _initialize() -> void:
	var glb: PackedScene = load("res://models/aster/aster_character.glb")
	var inst := glb.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	var lh := skel.find_bone("L_Hand")
	var rh := skel.find_bone("R_Hand")
	print("L_Hand global rest pos=", skel.get_bone_global_rest(lh).origin)
	print("R_Hand global rest pos=", skel.get_bone_global_rest(rh).origin)
	quit(0)
