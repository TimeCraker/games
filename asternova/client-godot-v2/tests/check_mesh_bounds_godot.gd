extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node3D = scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	var body: MeshInstance3D = inst.find_children("Aster_Body", "MeshInstance3D", true, false)[0]
	
	print("--- MESH BOUNDS IN GODOT ---")
	var aabb := body.get_aabb()
	print("AABB center=", aabb.get_center(), " size=", aabb.size)
	print("X min=", aabb.position.x, " max=", aabb.end.x)
	print("Y min=", aabb.position.y, " max=", aabb.end.y)
	print("Z min=", aabb.position.z, " max=", aabb.end.z)
	
	print("--- BONE HEAD & TAIL POSITIONS IN GODOT ---")
	for bname in ["Head", "R_Hand", "L_Hand", "Pelvis_L_Scabbard_Socket"]:
		var idx := skel.find_bone(bname)
		if idx >= 0:
			var gpose := skel.get_bone_global_rest(idx)
			print(bname, ": global_origin=", gpose.origin)
	quit(0)
