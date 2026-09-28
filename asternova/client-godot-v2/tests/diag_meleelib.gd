extends SceneTree

func _initialize() -> void:
	var mlib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var slib: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	print("MeleeLib anims:", mlib.get_animation_list())
	print("ShooterLib anims:", slib.get_animation_list())
	quit(0)
