extends SceneTree

func _init() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	print("Scene Root children:")
	for c in inst.get_children():
		print("  ", c.name, " (", c.get_class(), ")")
	var anim_players = inst.find_children("*", "AnimationPlayer", true, false)
	print("Found AnimationPlayers: ", anim_players.size())
	for ap in anim_players:
		print("  AP name: ", ap.name, " path: ", ap.get_path())
		for lib_name in ap.get_animation_library_list():
			var lib = ap.get_animation_library(lib_name)
			print("    lib [", lib_name, "]: ", lib.get_animation_list())
	
	var anim_tree: Resource = load("res://art/animations/aster_anim_tree.tres")
	print("AnimationTree loaded: ", anim_tree != null)
	
	var aster_lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	print("aster_animlib clips count: ", aster_lib.get_animation_list().size())
	print("has idle: ", aster_lib.has_animation("idle"), " has LightIdle: ", aster_lib.has_animation("LightIdle"))
	
	quit(0)
