extends SceneTree

func _initialize() -> void:
	var ps: PackedScene = load("res://scenes/entities/character_aster.tscn")
	var aster = ps.instantiate()
	var skel: Skeleton3D = aster.find_child("Skeleton3D", true, false)
	var idx := skel.find_bone("L_Upperarm")
	
	print("--- Bone Pose Meaning Test ---")
	print("L_Upperarm rest basis quat: ", skel.get_bone_rest(idx).basis.get_rotation_quaternion())
	print("L_Upperarm rest pose quat: ", skel.get_bone_pose_rotation(idx))
	print("L_Upperarm initial global pose: ", skel.get_bone_global_pose(idx).basis.get_rotation_quaternion())
	
	skel.set_bone_pose_rotation(idx, Quaternion.IDENTITY)
	print("After set_bone_pose_rotation(IDENTITY):")
	print("  get_bone_pose_rotation: ", skel.get_bone_pose_rotation(idx))
	print("  get_bone_global_pose: ", skel.get_bone_global_pose(idx).basis.get_rotation_quaternion())
	
	skel.set_bone_pose_rotation(idx, skel.get_bone_rest(idx).basis.get_rotation_quaternion())
	print("After set_bone_pose_rotation(rest_quat):")
	print("  get_bone_global_pose: ", skel.get_bone_global_pose(idx).basis.get_rotation_quaternion())

	quit(0)
