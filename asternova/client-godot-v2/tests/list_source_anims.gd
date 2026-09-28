extends SceneTree

func _initialize() -> void:
	var m_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var s_lib: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	
	print("--- MeleeLib Animations ---")
	for a in m_lib.get_animation_list():
		print("  ", a)
		
	print("\n--- ShooterLib Animations ---")
	for a in s_lib.get_animation_list():
		print("  ", a)
	quit(0)
