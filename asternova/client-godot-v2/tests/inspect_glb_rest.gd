extends SceneTree

func _initialize() -> void:
	print("=== Inspect Godot Bone Rest Transforms directly from GLB ===")
	var glb: PackedScene = load("res://models/aster/aster_character.glb")
	var inst := glb.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	
	for bname in ["R_Clavicle", "R_Upperarm", "R_Forearm", "R_Hand"]:
		var idx := skel.find_bone(bname)
		var rest := skel.get_bone_rest(idx)
		var g_rest := skel.get_bone_global_rest(idx)
		print(bname)
		print("  local rest pos=", rest.origin, " euler=", rad_to_deg(rest.basis.get_euler().x), ",", rad_to_deg(rest.basis.get_euler().y), ",", rad_to_deg(rest.basis.get_euler().z))
		print("  global rest pos=", g_rest.origin)
	
	quit(0)
