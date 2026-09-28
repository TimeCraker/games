extends SceneTree
func _initialize() -> void:
	for p in ["res://art/animations/MeleeLib.res", "res://art/animations/ShooterLib.res"]:
		var lib: AnimationLibrary = load(p)
		var alist := lib.get_animation_list()
		print("==== ", p, " (", alist.size(), ") ====")
		var names := PackedStringArray()
		for n in alist:
			names.append(n)
		print(" | ".join(names))
	quit(0)
