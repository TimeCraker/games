extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_source_probe.glb")
	if not scene:
		print("FAIL TO LOAD SOURCE")
		quit(1)
		return
	var inst: Node = scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	print("=== RAW SOURCE GLB BONES IN GODOT ===")
	for bname in ["Root", "Hip", "Pelvis", "Waist", "Spine01", "Spine02", "Head", "L_Upperarm", "R_Upperarm", "L_Thigh", "R_Thigh"]:
		var idx := skel.find_bone(bname)
		if idx >= 0:
			var grest := skel.get_bone_global_rest(idx)
			print(bname, ": grest_rot_deg=", grest.basis.get_euler() * 180.0 / PI, " grest_y_axis=", grest.basis.y)
	quit(0)
