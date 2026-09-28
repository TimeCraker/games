extends SceneTree

func _initialize() -> void:
	var path := "res://scenes/entities/character_aster.tscn"
	var char_aster: AsterRig = load(path).instantiate() as AsterRig
	get_root().add_child(char_aster)
	
	print("char_aster children: ", char_aster.get_children())
	for c in char_aster.get_children():
		print("  child: ", c.name, " (", c.get_class(), ")")
		for cc in c.get_children():
			print("    grandchild: ", cc.name, " (", cc.get_class(), ")")
			for ccc in cc.get_children():
				print("      great-grandchild: ", ccc.name, " (", ccc.get_class(), ")")
	quit(0)
