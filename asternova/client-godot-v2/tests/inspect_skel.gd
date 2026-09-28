extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	var skels = inst.find_children("*", "Skeleton3D", true, false)
	if skels.is_empty():
		print("No skeleton found!")
		quit(1)
		return
	var skel: Skeleton3D = skels[0]
	print("Skeleton name: ", skel.name, ", Bone count: ", skel.get_bone_count())
	for i in skel.get_bone_count():
		var bname := skel.get_bone_name(i)
		var rest := skel.get_bone_rest(i)
		var grest := skel.get_bone_global_rest(i)
		if bname in ["Root", "Hip", "Pelvis", "Waist", "Spine01", "Spine02", "Head", "L_Thigh", "R_Thigh"]:
			print("Bone: %-12s | rest_rot: %s | grest_pos: %s | grest_fwd (basis.z): %s" % [
				bname, rest.basis.get_euler(), grest.origin, grest.basis.z
			])
	quit(0)
