extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	var tester = RetargetTester.new()
	playground.add_child(tester)

class RetargetTester extends Node:
	var tick: int = 0
	var player: PlayerController = null
	var rig: AsterRig = null
	var skel: Skeleton3D = null
	var test_cam: Camera3D = null
	var artifact_dir := "C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165"

	const BONE_MAP := {
		"Root": "Root", "Hips": "Hip", "Spine": "Waist", "Chest": "Spine01",
		"UpperChest": "Spine02", "Neck": "NeckTwist01", "Head": "Head",
		"LeftShoulder": "L_Clavicle", "RightShoulder": "R_Clavicle",
		"LeftUpperArm": "L_Upperarm", "RightUpperArm": "R_Upperarm",
		"LeftLowerArm": "L_Forearm", "RightLowerArm": "R_Forearm",
		"LeftHand": "L_Hand", "RightHand": "R_Hand",
		"LeftUpperLeg": "L_Thigh", "RightUpperLeg": "R_Thigh",
		"LeftLowerLeg": "L_Calf", "RightLowerLeg": "R_Calf",
		"LeftFoot": "L_Foot", "RightFoot": "R_Foot",
		"LeftToes": "L_ToeBase", "RightToes": "R_ToeBase",
	}

	const SRC_PARENTS := {
		"Root": "", "Hips": "Root", "Spine": "Hips", "Chest": "Spine", "UpperChest": "Chest",
		"Neck": "UpperChest", "Head": "Neck",
		"LeftShoulder": "UpperChest", "RightShoulder": "UpperChest",
		"LeftUpperArm": "LeftShoulder", "RightUpperArm": "RightShoulder",
		"LeftLowerArm": "LeftUpperArm", "RightLowerArm": "RightUpperArm",
		"LeftHand": "LeftLowerArm", "RightHand": "RightLowerArm",
		"LeftUpperLeg": "Hips", "RightUpperLeg": "Hips",
		"LeftLowerLeg": "LeftUpperLeg", "RightLowerLeg": "RightUpperLeg",
		"LeftFoot": "LeftLowerLeg", "RightFoot": "RightLowerLeg",
		"LeftToes": "LeftFoot", "RightToes": "RightFoot",
	}

	var d_gr := {}
	var s_gr := {}
	var melee_lib: AnimationLibrary
	var shooter_lib: AnimationLibrary
	var q_rot_180 := Quaternion(Vector3.UP, PI)

	func _ready() -> void:
		var scene_root := get_parent()
		player = scene_root.get_node_or_null("Player") as PlayerController
		rig = player.visual_root.get_node_or_null("CharacterAster") as AsterRig
		skel = rig.skeleton
		rig.anim_tree.active = false
		rig.anim_player.stop()

		test_cam = Camera3D.new()
		add_child(test_cam)

		melee_lib = load("res://art/animations/MeleeLib.res")
		shooter_lib = load("res://art/animations/ShooterLib.res")

		for src_b in BONE_MAP:
			var dst_b: String = BONE_MAP[src_b]
			var idx := skel.find_bone(dst_b)
			if idx >= 0:
				d_gr[src_b] = skel.get_bone_global_rest(idx).basis.get_rotation_quaternion().normalized()

		var tpose: Animation = shooter_lib.get_animation("tpose")
		var s_local_rest := {}
		for t in tpose.get_track_count():
			if tpose.track_get_type(t) == Animation.TYPE_ROTATION_3D:
				var bname := String(tpose.track_get_path(t).get_subname(0))
				s_local_rest[bname] = tpose.rotation_track_interpolate(t, 0.0).normalized()

		for b in SRC_PARENTS:
			var chain: Array[String] = []
			var curr: String = b
			while curr != "":
				chain.push_front(curr)
				curr = SRC_PARENTS[curr]
			var q := Quaternion.IDENTITY
			for node_b in chain:
				q = q * s_local_rest.get(node_b, Quaternion.IDENTITY)
			# Transform source rest to Aster world space (+Z forward -> -Z forward)
			s_gr[b] = (q_rot_180 * q.normalized() * q_rot_180.inverse()).normalized()

	func _apply_pose(anim: Animation, time: float) -> void:
		var src_local := {}
		for t in anim.get_track_count():
			if anim.track_get_type(t) == Animation.TYPE_ROTATION_3D:
				var bname := String(anim.track_get_path(t).get_subname(0))
				src_local[bname] = anim.rotation_track_interpolate(t, time).normalized()

		var s_g := {}
		for b in SRC_PARENTS:
			var chain: Array[String] = []
			var curr: String = b
			while curr != "":
				chain.push_front(curr)
				curr = SRC_PARENTS[curr]
			var q := Quaternion.IDENTITY
			for node_b in chain:
				q = q * src_local.get(node_b, Quaternion.IDENTITY)
			# Transform source global pose to Aster world space
			s_g[b] = (q_rot_180 * q.normalized() * q_rot_180.inverse()).normalized()

		var d_g := {}
		for b in BONE_MAP:
			if not s_g.has(b) or not s_gr.has(b) or not d_gr.has(b):
				continue
			var delta_g: Quaternion = (s_g[b] * (s_gr[b] as Quaternion).inverse()).normalized()
			d_g[b] = (delta_g * (d_gr[b] as Quaternion)).normalized()

		skel.reset_bone_poses()
		for b in BONE_MAP:
			if b == "Root" or not d_g.has(b):
				continue
			var dst_b: String = BONE_MAP[b]
			var idx := skel.find_bone(dst_b)
			if idx < 0:
				continue
			var parent_src: String = SRC_PARENTS[b]
			var q_loc: Quaternion
			if parent_src != "" and d_g.has(parent_src):
				q_loc = (d_g[parent_src].inverse() * d_g[b]).normalized()
			else:
				q_loc = d_g[b]
			skel.set_bone_pose_rotation(idx, q_loc)

	func _set_cam(pos: Vector3, look_pos: Vector3) -> void:
		test_cam.global_position = pos
		test_cam.look_at(look_pos, Vector3.UP)
		test_cam.make_current()

	func _physics_process(_delta: float) -> void:
		tick += 1
		var cpos: Vector3 = player.global_position

		if tick == 5:
			# Test ShooterLib "idle" with 180-aligned retargeting
			_apply_pose(shooter_lib.get_animation("idle"), 0.0)
			# Front view of full body (camera at -Z looking towards +Z)
			_set_cam(cpos + Vector3(0.0, 0.85, -2.2), cpos + Vector3(0.0, 0.82, 0.0))
		elif tick == 10:
			_save_frame(artifact_dir + "/test_180_shooter_idle_front.png")

		elif tick == 15:
			# Test MeleeLib "Slash1" with 180-aligned retargeting
			_apply_pose(melee_lib.get_animation("Slash1"), 0.35)
			_set_cam(cpos + Vector3(0.0, 0.85, -2.2), cpos + Vector3(0.0, 0.82, 0.0))
		elif tick == 20:
			_save_frame(artifact_dir + "/test_180_slash1_front.png")
			get_tree().quit(0)

	func _save_frame(path: String) -> void:
		var img := get_viewport().get_texture().get_image()
		if img:
			var err := img.save_png(path)
			print("Saved [err=", err, "]: ", path)
