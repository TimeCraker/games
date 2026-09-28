extends SceneTree

func _initialize() -> void:
	var melee: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var shooter: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	
	print("=== MeleeLib Clips ===")
	print(melee.get_animation_list())
	var a_melee := melee.get_animation("LightIdle")
	print("\nTracks in MeleeLib/LightIdle:")
	for t in a_melee.get_track_count():
		print("  ", a_melee.track_get_path(t))

	print("\n=== ShooterLib Clips ===")
	print(shooter.get_animation_list())
	var a_shoot := shooter.get_animation("idle")
	print("\nTracks in ShooterLib/idle:")
	for t in a_shoot.get_track_count():
		print("  ", a_shoot.track_get_path(t))

	quit(0)
