extends SceneTree

func _initialize() -> void:
	var melee: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var shooter: AnimationLibrary = load("res://art/animations/ShooterLib.res")

	print("=== MeleeLib Idle 剪辑 ===")
	for a in melee.get_animation_list():
		if a.to_lower().contains("idle"):
			print("  Melee: ", a)

	print("=== ShooterLib Idle 剪辑 ===")
	for a in shooter.get_animation_list():
		if a.to_lower().contains("idle"):
			print("  Shooter: ", a)

	quit(0)
