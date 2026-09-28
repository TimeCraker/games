@tool
extends SceneTree

func _init() -> void:
	var packed = load("res://models/aster/aster_character.glb")
	var scene = packed.instantiate()
	var skel: Skeleton3D = scene.find_child("Skeleton3D", true, false)
	if skel:
		print("Skeleton bone count: ", skel.get_bone_count())
		for b in range(skel.get_bone_count()):
			print("  bone ", b, ": ", skel.get_bone_name(b))
	quit(0)
