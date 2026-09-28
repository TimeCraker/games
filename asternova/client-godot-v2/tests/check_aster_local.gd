extends SceneTree

func _initialize() -> void:
	var skel_scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = skel_scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]

	print("=== Aster Rest 局部基底 ===")
	for bname in ["Hip", "Pelvis", "L_Thigh", "R_Thigh", "L_Calf", "R_Calf", "L_Foot", "R_Foot", "L_Upperarm", "R_Upperarm", "L_Forearm", "R_Forearm"]:
		var idx := skel.find_bone(bname)
		if idx >= 0:
			var rest := skel.get_bone_rest(idx)
			print("Bone %-14s local rest basis: X=%s Y=%s Z=%s" % [
				bname, rest.basis.x.snapped(Vector3(0.01,0.01,0.01)), rest.basis.y.snapped(Vector3(0.01,0.01,0.01)), rest.basis.z.snapped(Vector3(0.01,0.01,0.01))])

	quit(0)
