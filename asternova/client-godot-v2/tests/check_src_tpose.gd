extends SceneTree

func _initialize() -> void:
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose: Animation = null
	for a in melee_lib.get_animation_list():
		if a.to_lower() == "tpose":
			tpose = melee_lib.get_animation(a)
			break
	
	const SRC_PARENTS := {
		"Root": "", "Hips": "Root", "Spine": "Hips", "Chest": "Spine", "UpperChest": "Chest",
		"Neck": "UpperChest", "Head": "Neck",
		"LeftUpperLeg": "Hips", "RightUpperLeg": "Hips"
	}
	
	var src_locals := {}
	for t in tpose.get_track_count():
		var bname = String(tpose.track_get_path(t).get_subname(0))
		if tpose.track_get_type(t) == Animation.TYPE_ROTATION_3D:
			src_locals[bname] = tpose.rotation_track_interpolate(t, 0.0)
	
	var src_globals := {}
	for b in ["Root", "Hips", "Spine", "Chest", "UpperChest", "Head", "LeftUpperArm", "RightUpperArm", "LeftUpperLeg", "RightUpperLeg"]:
		var p = SRC_PARENTS.get(b, "")
		var local = src_locals.get(b, Quaternion.IDENTITY)
		var p_glob = src_globals.get(p, Quaternion.IDENTITY) if p != "" else Quaternion.IDENTITY
		src_globals[b] = p_glob * local
		var b3d = Basis(src_globals[b])
		print("SRC ", b, ": rot_deg=", b3d.get_euler() * 180.0 / PI, " Y_axis=", b3d.y)
	quit(0)
