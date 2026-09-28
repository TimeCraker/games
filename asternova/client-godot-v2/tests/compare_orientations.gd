extends SceneTree

func _initialize() -> void:
	print("=== Bone Rest Orientation Comparison ===")
	var aster_scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst := aster_scene.instantiate()
	var aster_skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose: Animation = melee_lib.get_animation("TPose")
	
	# 查看几个关键骨骼：Hips, Spine, RightUpperArm, LeftUpperArm, RightUpperLeg, LeftUpperLeg
	const BONES := [
		["Hips", "Hip"],
		["Chest", "Spine01"],
		["RightUpperArm", "R_Upperarm"],
		["LeftUpperArm", "L_Upperarm"],
		["RightUpperLeg", "R_Thigh"],
		["LeftUpperLeg", "L_Thigh"],
	]
	
	for pair in BONES:
		var src_name: String = pair[0]
		var dst_name: String = pair[1]
		
		var dst_idx := aster_skel.find_bone(dst_name)
		var dst_gt := aster_skel.get_bone_global_rest(dst_idx)
		
		print("\n[%s -> %s]" % [src_name, dst_name])
		print("  Aster Global Rest: pos=%s" % [dst_gt.origin])
		print("    basis.x (right) = %s" % [dst_gt.basis.x])
		print("    basis.y (up/bone) = %s" % [dst_gt.basis.y])
		print("    basis.z (front) = %s" % [dst_gt.basis.z])
	
	quit(0)
