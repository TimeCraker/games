extends SceneTree
func _initialize() -> void:
	for cls in ClassDB.get_class_list():
		for m in ClassDB.class_get_method_list(cls, true):
			if "retarget" in String(m.name).to_lower():
				print(cls, " -> ", m.name)
	for cls in ["AnimationLibrary", "Animation", "BoneMap", "Skeleton3D", "AnimationMixer"]:
		for m in ClassDB.class_get_method_list(cls, true):
			var n := String(m.name).to_lower()
			if "retarget" in n or "remap" in n:
				print("own: ", cls, " -> ", m.name)
	quit(0)
