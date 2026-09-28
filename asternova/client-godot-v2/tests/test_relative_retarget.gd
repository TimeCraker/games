extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	var tester = RelativeRetargetTester.new()
	tester.name = "RelativeRetargetTester"
	playground.add_child(tester)

class RelativeRetargetTester extends Node:
	var tick: int = 0
	var player: PlayerController = null
	var rig: AsterRig = null
	var skel: Skeleton3D = null
	var cam: Camera3D = null
	var anim_player: AnimationPlayer = null
	var test_lib: AnimationLibrary = null
	var artifact_dir := "C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165"

	const BONE_MAP := {
		"Root": "Root", "Hips": "Hip", "Spine": "Waist", "Chest": "Spine01", "UpperChest": "Spine02",
		"Neck": "NeckTwist01", "Head": "Head",
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

	func _ready() -> void:
		var scene_root := get_parent()
		player = scene_root.get_node_or_null("Player") as PlayerController
		rig = player.visual_root.get_node_or_null("CharacterAster") as AsterRig
		if rig.anim_tree:
			rig.anim_tree.active = false
		
		skel = rig.find_child("Skeleton3D", true, false) as Skeleton3D
		anim_player = rig.find_child("AnimationPlayer", true, false) as AnimationPlayer
		if not anim_player:
			anim_player = AnimationPlayer.new()
			anim_player.name = "TestAnimPlayer"
			skel.get_parent().add_child(anim_player)
		
		cam = Camera3D.new()
		cam.fov = 36.0
		add_child(cam)

		# 构建测试库
		test_lib = _build_test_lib()
		anim_player.add_animation_library("test", test_lib)
		print("Test AnimationLibrary built and added to AnimationPlayer")

	func _build_test_lib() -> AnimationLibrary:
		var melee: AnimationLibrary = load("res://art/animations/MeleeLib.res")
		var tpose: Animation = melee.get_animation("TPose")
		
		# 1. 采集源局部 Rest 与全局 Rest (RAW，绝不施加任何硬编码 180 翻转)
		var s_local_rest := {}
		for t in tpose.get_track_count():
			if tpose.track_get_type(t) == Animation.TYPE_ROTATION_3D:
				var bname := String(tpose.track_get_path(t).get_subname(0))
				s_local_rest[bname] = tpose.rotation_track_interpolate(t, 0.0).normalized()

		var s_gr := {}
		for b: String in SRC_PARENTS:
			var chain: Array[String] = []
			var curr: String = b
			while curr != "":
				chain.push_front(curr)
				curr = SRC_PARENTS[curr]
			var q := Quaternion.IDENTITY
			for node_b in chain:
				q = q * s_local_rest.get(node_b, Quaternion.IDENTITY)
			s_gr[b] = q.normalized()

		# 2. 采集目标骨架 Rest 与对齐四元数 R_align(b) = D_gr(b)⁻¹ · S_gr(b)
		var d_gr := {}
		var d_local_rest := {}
		var r_align := {}
		for src_b: String in BONE_MAP:
			var dst_b: String = BONE_MAP[src_b]
			var idx := skel.find_bone(dst_b)
			if idx < 0:
				continue
			d_gr[src_b] = skel.get_bone_global_rest(idx).basis.get_rotation_quaternion().normalized()
			d_local_rest[src_b] = skel.get_bone_rest(idx).basis.get_rotation_quaternion().normalized()
			# 基底对齐四元数：将源局部旋转映射至目标局部空间
			# R_align = D_gr⁻¹ · S_gr
			r_align[src_b] = (d_gr[src_b].inverse() * s_gr[src_b]).normalized()

		var out := AnimationLibrary.new()
		for anim_name in ["LightIdle", "Slash1", "LightRunning"]:
			if not melee.has_animation(anim_name):
				continue
			var src_anim := melee.get_animation(anim_name)
			var out_anim := Animation.new()
			out_anim.length = src_anim.length
			out_anim.step = src_anim.step
			out_anim.loop_mode = Animation.LOOP_LINEAR if anim_name != "Slash1" else Animation.LOOP_NONE

			for t in src_anim.get_track_count():
				if src_anim.track_get_type(t) != Animation.TYPE_ROTATION_3D:
					continue
				var src_b := String(src_anim.track_get_path(t).get_subname(0))
				if not BONE_MAP.has(src_b):
					continue
				var dst_b: String = BONE_MAP[src_b]
				var nt := out_anim.add_track(Animation.TYPE_ROTATION_3D)
				out_anim.track_set_path(nt, NodePath("Skeleton3D:%s" % dst_b))

				var r_a: Quaternion = r_align[src_b]
				var d_rest: Quaternion = d_local_rest[src_b]
				var s_rest: Quaternion = s_local_rest.get(src_b, Quaternion.IDENTITY)

				for k in src_anim.track_get_key_count(t):
					var time: float = src_anim.track_get_key_time(t, k)
					var q_src: Quaternion = src_anim.rotation_track_interpolate(t, time).normalized()
					
					# 局部增量 Delta_src = q_src · s_rest⁻¹
					var delta_src: Quaternion = (q_src * s_rest.inverse()).normalized()
					# 映射到目标局部空间：Delta_dst = R_align · Delta_src · R_align⁻¹
					var delta_dst: Quaternion = (r_a * delta_src * r_a.inverse()).normalized()
					# 目标局部旋转：q_out = Delta_dst · d_rest
					var q_out: Quaternion = (delta_dst * d_rest).normalized()
					
					out_anim.rotation_track_insert_key(nt, time, q_out)
			
			out.add_animation(anim_name, out_anim)
			print("Built test anim: ", anim_name)

		return out

	func _physics_process(_delta: float) -> void:
		tick += 1
		var cpos: Vector3 = player.global_position

		# 1. 播放新版 LightIdle
		if tick == 10:
			anim_player.play("test/LightIdle")
		elif tick == 25:
			# 待命立绘全身正面
			cam.global_position = cpos + Vector3(0.0, 0.85, -2.6)
			cam.look_at(cpos + Vector3(0.0, 0.80, 0.0), Vector3.UP)
			cam.make_current()
		elif tick == 30:
			_save(artifact_dir + "/rel_01_idle_front.png")

		elif tick == 35:
			# 待命双脚特写
			cam.global_position = cpos + Vector3(0.0, 0.16, -0.85)
			cam.look_at(cpos + Vector3(0.0, 0.10, 0.0), Vector3.UP)
		elif tick == 40:
			_save(artifact_dir + "/rel_02_idle_feet_closeup.png")

		# 2. 播放新版 LightRunning
		elif tick == 45:
			anim_player.play("test/LightRunning")
		elif tick == 60:
			# 跑步全身侧面
			cam.global_position = cpos + Vector3(-2.8, 0.85, 0.0)
			cam.look_at(cpos + Vector3(0.0, 0.80, 0.0), Vector3.UP)
		elif tick == 65:
			_save(artifact_dir + "/rel_03_run_side.png")

		# 3. 播放新版 Slash1 (挥砍)
		elif tick == 70:
			rig.draw_sword()
			anim_player.play("test/Slash1")
		elif tick == 85:
			# 挥砍定格全身正面
			cam.global_position = cpos + Vector3(0.0, 0.85, -2.6)
			cam.look_at(cpos + Vector3(0.0, 0.80, 0.0), Vector3.UP)
		elif tick == 90:
			_save(artifact_dir + "/rel_04_slash1_front.png")
			print("=== 测试截图已全部捕获 ===")
			get_tree().quit(0)

	func _save(path: String) -> void:
		var img := get_viewport().get_texture().get_image()
		if img:
			img.save_png(path)
			print("Saved: ", path)
