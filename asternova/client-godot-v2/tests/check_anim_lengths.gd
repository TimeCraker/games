extends SceneTree

func _init() -> void:
	var glb: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = glb.instantiate()
	var ap: AnimationPlayer = inst.get_node("AnimationPlayer") as AnimationPlayer
	for name in ["Idle", "Walk", "Jog_Fwd", "Sprint"]:
		if ap.has_animation(name):
			var a := ap.get_animation(name)
			print(name, " length: ", a.length, " loop: ", a.loop_mode)
	quit(0)
