extends SceneTree

func _initialize() -> void:
	var glb: PackedScene = load("res://models/aster/aster_character.glb")
	var inst := glb.instantiate()
	var skel: Skeleton3D = inst.find_child("Skeleton3D", true, false) as Skeleton3D
	if not skel:
		print("No Skeleton3D found")
		quit(1)
		return

	var l_up := skel.find_bone("L_Upperarm")
	var l_low := skel.find_bone("L_Forearm")
	var r_up := skel.find_bone("R_Upperarm")
	var r_low := skel.find_bone("R_Forearm")

	var l_up_rest := skel.get_bone_global_rest(l_up)
	var l_low_rest := skel.get_bone_global_rest(l_low)
	var r_up_rest := skel.get_bone_global_rest(r_up)
	var r_low_rest := skel.get_bone_global_rest(r_low)

	var l_dir := (l_low_rest.origin - l_up_rest.origin).normalized()
	var r_dir := (r_low_rest.origin - r_up_rest.origin).normalized()

	print("L_Upperarm global origin: ", l_up_rest.origin)
	print("L_Forearm global origin: ", l_low_rest.origin)
	print("L_Upperarm actual bone vector: ", l_dir)
	print("L_Upperarm basis.x: ", l_up_rest.basis.x)
	print("L_Upperarm basis.y: ", l_up_rest.basis.y)
	print("L_Upperarm basis.z: ", l_up_rest.basis.z)

	print("R_Upperarm global origin: ", r_up_rest.origin)
	print("R_Forearm global origin: ", r_low_rest.origin)
	print("R_Upperarm actual bone vector: ", r_dir)
	print("R_Upperarm basis.x: ", r_up_rest.basis.x)
	print("R_Upperarm basis.y: ", r_up_rest.basis.y)
	print("R_Upperarm basis.z: ", r_up_rest.basis.z)

	quit(0)
