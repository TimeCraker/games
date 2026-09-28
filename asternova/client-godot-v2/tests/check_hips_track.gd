extends SceneTree

func _initialize() -> void:
	var scn: Node = load("res://scenes/entities/character_aster.tscn").instantiate()
	root.add_child(scn)
	var ap: AnimationPlayer = scn.find_child("AnimationPlayer", true, false)
	var a1: Animation = ap.get_animation("LightIdle")
	var a2: Animation = ap.get_animation("LightIdle2")
	print("LightIdle length=", a1.length, " tracks=", a1.get_track_count())
	print("LightIdle track[0]=", a1.track_get_path(0), " track[1]=", a1.track_get_path(1))
	print("LightIdle2 length=", a2.length, " tracks=", a2.get_track_count())
	print("LightIdle2 track[0]=", a2.track_get_path(0), " track[1]=", a2.track_get_path(1))
	quit(0)
