@tool
extends SceneTree

func _init() -> void:
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	var anim = lib.get_animation("idle")
	for t in range(anim.get_track_count()):
		print(t, ": ", anim.track_get_path(t))
	quit(0)
