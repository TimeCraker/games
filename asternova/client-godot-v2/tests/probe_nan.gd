extends SceneTree
func _initialize() -> void:
	var glb: PackedScene = load("res://models/aster/aster_assembled.glb")
	var holder: Node3D = Node3D.new()
	root.add_child(holder)
	var inst: Node = glb.instantiate()
	holder.add_child(inst)
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	var player := AnimationPlayer.new()
	holder.add_child(player)
	player.root_node = player.get_path_to(skel.get_parent())
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	player.add_animation_library("", lib)
	# 先打印库内 idle 的 Hip 旋转首键
	var a: Animation = lib.get_animation("idle")
	var ti := a.find_track(NodePath("Skeleton3D:Hip"), Animation.TYPE_ROTATION_3D)
	print("idle Hip rot keys=", a.track_get_key_count(ti), " k0=", a.rotation_track_interpolate(ti, 0.0))
	player.play("idle")
	for i in 5:
		await physics_frame
	var nan_count := 0
	var sample := ""
	for b in 43:
		var p := skel.get_bone_global_pose(b)
		if not (p.origin.is_finite() and p.basis.determinant() == p.basis.determinant()):
			nan_count += 1
		elif b < 3:
			sample += " %s=%s" % [skel.get_bone_name(b), str(p.origin.snapped(Vector3(0.01,0.01,0.01)))]
	print("nan_bones=", nan_count, " sample:", sample)
	print("hipY_world=", (skel.global_transform * skel.get_bone_global_pose(skel.find_bone("Hip")).origin).y)
	quit(0)
