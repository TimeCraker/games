extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node3D = scene.instantiate()
	var skel: Skeleton3D = inst.find_child("Skeleton3D", true, false) as Skeleton3D
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	var anim: Animation = lib.get_animation("idle")
	
	print("Skeleton bone count: ", skel.get_bone_count())
	for bname in ["R_Upperarm", "R_Forearm", "R_Hand", "L_Upperarm", "L_Forearm", "L_Hand"]:
		var idx = skel.find_bone(bname)
		var rest_gt = skel.get_bone_global_rest(idx)
		print("Rest Global ", bname, ": origin=", rest_gt.origin)
	
	# Apply first frame of idle
	for t in anim.get_track_count():
		var p: NodePath = anim.track_get_path(t)
		var bname: String = p.get_subname(0) if p.get_subname_count() > 0 else ""
		var idx = skel.find_bone(bname)
		if idx >= 0:
			var rot: Quaternion = anim.track_get_key_value(t, 0)
			skel.set_bone_pose_rotation(idx, rot)
	
	print("\n--- Posed (Idle Frame 0) Global Transforms ---")
	for bname in ["R_Upperarm", "R_Forearm", "R_Hand", "L_Upperarm", "L_Forearm", "L_Hand"]:
		var idx = skel.find_bone(bname)
		var posed_gt = skel.get_bone_global_pose(idx)
		print("Posed Global ", bname, ": origin=", posed_gt.origin)
	
	quit(0)
