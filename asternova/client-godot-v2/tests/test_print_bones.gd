extends SceneTree

func _init() -> void:
	var glb = load("res://models/aster/aster_character.glb").instantiate()
	var skel: Skeleton3D = glb.find_child("Skeleton3D", true, false)
	print("Total bones:", skel.get_bone_count())
	for i in range(skel.get_bone_count()):
		var rest_pos = skel.get_bone_rest(i).origin
		var global_rest = skel.get_bone_global_rest(i).origin
		print("Bone [%2d] %-25s rest=%s global_x=%+.3f" % [i, skel.get_bone_name(i), rest_pos, global_rest.x])
	quit()
