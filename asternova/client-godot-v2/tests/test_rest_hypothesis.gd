extends SceneTree

func _initialize() -> void:
	print("=== Test Rest Pose Keyframe Hypothesis ===")
	var glb: PackedScene = load("res://models/aster/aster_character.glb")
	var inst := glb.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	
	for bname in ["R_Upperarm", "R_Forearm", "R_Hand", "L_Thigh", "R_Thigh"]:
		var idx := skel.find_bone(bname)
		var rest_q := skel.get_bone_rest(idx).basis.get_rotation_quaternion()
		var eu := rest_q.get_euler()
		print("%-12s rest_local euler deg=(%.1f, %.1f, %.1f)" % [bname, rad_to_deg(eu.x), rad_to_deg(eu.y), rad_to_deg(eu.z)])
	
	quit(0)
