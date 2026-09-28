extends SceneTree

func _initialize() -> void:
	var scene_res: PackedScene = load("res://scenes/entities/character_aster.tscn")
	var inst := scene_res.instantiate()
	print("--- CharacterAster Children Tree ---")
	_print_tree(inst, "")
	quit(0)

func _print_tree(node: Node, indent: String) -> void:
	print(indent, node.name, " (", node.get_class(), ")")
	for child in node.get_children():
		_print_tree(child, indent + "  ")
