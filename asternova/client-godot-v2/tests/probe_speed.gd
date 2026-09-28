extends SceneTree
func _initialize() -> void:
	var t := AnimationTree.new()
	var names: Array = []
	for p in t.get_property_list():
		var n := String(p.name).to_lower()
		if "speed" in n or "scale" in n or "playback" in n or "determinis" in n:
			names.append(p.name + ":" + str(p.type))
	print(names)
	quit(0)
