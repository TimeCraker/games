extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	
	print("=== Aster Bones Rest Pose in Godot ===")
	for bname in ["Root", "Hip", "Pelvis", "Waist", "Spine01", "Spine02", "Head", "L_Thigh", "R_Thigh"]:
		var idx := skel.find_bone(bname)
		if idx >= 0:
			var rest := skel.get_bone_rest(idx)
			var grest := skel.get_bone_global_rest(idx)
			print(bname, ":\n  rest_rot_deg=", rest.basis.get_euler() * 180.0 / PI, 
				  "\n  grest_rot_deg=", grest.basis.get_euler() * 180.0 / PI,
				  "\n  grest_y_axis(tail dir)=", grest.basis.y)
	quit(0)
