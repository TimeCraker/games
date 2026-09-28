@tool
extends SceneTree

func _init() -> void:
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	if not lib:
		print("Failed to load aster_animlib.res")
		quit(1)
		return
	print("Anim count in lib: ", lib.get_animation_list().size())
	for anim_name in ["idle", "LightWalking", "LightRunning", "Slash1"]:
		if lib.has_animation(anim_name):
			var anim = lib.get_animation(anim_name)
			print("Anim: ", anim_name, " length: ", anim.length, " tracks: ", anim.get_track_count())
			var bones = []
			for t in range(anim.get_track_count()):
				var path = anim.track_get_path(t)
				bones.append(str(path))
			print("  sample tracks: ", bones.slice(0, 8))
	quit(0)
