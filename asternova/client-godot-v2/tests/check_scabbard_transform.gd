extends SceneTree

func _initialize() -> void:
	var path := "res://scenes/entities/character_aster.tscn"
	var char_aster: AsterRig = load(path).instantiate() as AsterRig
	get_root().add_child(char_aster)

	var sk: Skeleton3D = char_aster.skeleton
	var idx := sk.find_bone("Pelvis_L_Scabbard_Socket")
	if idx != -1:
		print("Pelvis_L_Scabbard_Socket rest pose:")
		print("  origin: ", sk.get_bone_rest(idx).origin)
		print("  rotation_degrees: ", sk.get_bone_rest(idx).basis.get_euler() * 180.0 / PI)
		print("  parent: ", sk.get_bone_name(sk.get_bone_parent(idx)))

	var scabbard = char_aster.find_child("Katana_Scabbard", true, false) as MeshInstance3D
	if scabbard:
		print("Katana_Scabbard transform: ", scabbard.transform)
		print("Katana_Scabbard AABB: ", scabbard.get_aabb())

	quit(0)
