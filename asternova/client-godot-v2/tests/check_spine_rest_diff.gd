extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	
	for bname in ["Hip", "Pelvis", "Waist", "Spine01", "Spine02"]:
		var idx := skel.find_bone(bname)
		var gt := skel.get_bone_global_rest(idx)
		var q := gt.basis.get_rotation_quaternion()
		print(bname, " global_rest rot_deg=", gt.basis.get_euler() * 180.0 / PI, " quat=", q)
		
	var w_idx := skel.find_bone("Waist")
	var s_idx := skel.find_bone("Spine01")
	var q_w := skel.get_bone_global_rest(w_idx).basis.get_rotation_quaternion()
	var q_s := skel.get_bone_global_rest(s_idx).basis.get_rotation_quaternion()
	var diff := q_w.inverse() * q_s
	print("Diff from Waist to Spine01 in rest: ", Basis(diff).get_euler() * 180.0 / PI)
	quit(0)
