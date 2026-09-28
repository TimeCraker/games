extends SceneTree

func _init() -> void:
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var shooter_lib: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	print("MeleeLib idle 剪辑:")
	for n in melee_lib.get_animation_list():
		if "idle" in n.to_lower():
			print("  ", n)
	print("ShooterLib idle 剪辑:")
	for n in shooter_lib.get_animation_list():
		if "idle" in n.to_lower():
			print("  ", n)
	quit(0)
