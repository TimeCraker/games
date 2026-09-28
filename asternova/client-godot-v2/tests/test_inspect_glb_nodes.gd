extends SceneTree

func _init() -> void:
	var glb: PackedScene = load("res://models/aster/aster_character.glb")
	var inst = glb.instantiate()
	root.add_child(inst)
	
	print("\n=== GLB Hierarchy ===")
	_print_tree(inst, "")
	quit()

func _print_tree(node: Node, indent: String) -> void:
	var extra = ""
	if node is Node3D:
		extra = " pos=%s rot_deg=%s scale=%s" % [node.position, node.rotation_degrees, node.scale]
	print("%s%s (%s)%s" % [indent, node.name, node.get_class(), extra])
	for c in node.get_children():
		_print_tree(c, indent + "  ")
