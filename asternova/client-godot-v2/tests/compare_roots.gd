extends SceneTree

func _initialize() -> void:
	var shooter_lib: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	var tpose: Animation = shooter_lib.get_animation("tpose")
	print("--- SHOOTER TPOSE TRACKS ---")
	for t in tpose.get_track_count():
		var p := String(tpose.track_get_path(t))
		if "Root" in p or "Hips" in p or "Spine" in p:
			print(p, " rot: ", tpose.rotation_track_interpolate(t, 0.0).get_euler() * 180.0 / PI)

	var char_aster = load("res://models/aster/aster_character.glb").instantiate()
	var sk: Skeleton3D = char_aster.find_child("Skeleton3D", true, false)
	print("--- ASTER REST ---")
	for bname in ["Root", "Hip", "Waist", "Spine01", "Spine02"]:
		var idx = sk.find_bone(bname)
		var rest_l = sk.get_bone_rest(idx)
		var rest_g = sk.get_bone_global_rest(idx)
		print(bname, " local rot: ", rest_l.basis.get_euler() * 180.0 / PI, " global rot: ", rest_g.basis.get_euler() * 180.0 / PI)
	quit(0)
