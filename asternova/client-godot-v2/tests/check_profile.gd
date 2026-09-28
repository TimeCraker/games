extends SceneTree

func _initialize() -> void:
	var prof := SkeletonProfileHumanoid.new()
	print("--- SkeletonProfileHumanoid Standards ---")
	print("root_bone: ", prof.root_bone)
	print("scale_base_bone: ", prof.scale_base_bone)
	for i in prof.bone_size:
		var bn := prof.get_bone_name(i)
		if bn in ["Hips", "Spine", "Head", "LeftUpperArm", "RightUpperArm", "LeftUpperLeg", "RightUpperLeg"]:
			print(bn, ": parent=", prof.get_bone_parent(i))
	quit(0)
