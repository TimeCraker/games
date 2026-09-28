extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	var tester = PerfectRetargetTester.new()
	tester.name = "PerfectRetargetTester"
	playground.add_child(tester)

class PerfectRetargetTester extends Node:
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

		test_lib = _build_perfect_lib()
		anim_player.add_animation_library("perf_test", test_lib)
		print("Perfect Retarget AnimationLibrary built!")

	func _build_perfect_lib() -> AnimationLibrary:
		var melee: AnimationLibrary = load("res://art/animations/MeleeLib.res")
		var shooter: AnimationLibrary = load("res://art/animations/ShooterLib.res")
		var tpose_m: Animation = melee.get_animation("TPose")
		var tpose_s: Animation = shooter.get_animation("tpose")
		
		# 1. 采集源局部 Rest 与全局 Rest (经 180° Y 对齐至 -Z 前向)
		var q_rot_180 := Quaternion(Vector3.UP, PI)
		var s_gr_dict := {"melee": {}, "shooter": {}}
		for lib_info in [["melee", tpose_m], ["shooter", tpose_s]]:
			var key: String = lib_info[0]
			var calib: Animation = lib_info[1]
			var local_rest := {}
			for t in calib.get_track_count():
				if calib.track_get_type(t) == Animation.TYPE_ROTATION_3D:
					var bname := String(calib.track_get_path(t).get_subname(0))
					local_rest[bname] = calib.rotation_track_interpolate(t, 0.0).normalized()
			
			var composed: Dictionary = s_gr_dict[key]
			for b: String in SRC_PARENTS:
				var chain: Array[String] = []
				var curr: String = b
				while curr != "":
					chain.push_front(curr)
					curr = SRC_PARENTS[curr]
				var q := Quaternion.IDENTITY
				for node_b in chain:
					q = q * local_rest.get(node_b, Quaternion.IDENTITY)
				composed[b] = (q_rot_180 * q.normalized() * q_rot_180.inverse()).normalized()

		# 2. 采集 Aster 目标骨架的全局 Rest，并对手臂应用 A-Pose -> T-Pose 自动校准
		var d_gr := {}
		var l_idx := skel.find_bone("L_Upperarm")
		var r_idx := skel.find_bone("R_Upperarm")
		var l_arm_rest_y := skel.get_bone_global_rest(l_idx).basis.y
		var r_arm_rest_y := skel.get_bone_global_rest(r_idx).basis.y
		var q_tpose_l := Quaternion(l_arm_rest_y, Vector3(-1, 0, 0))
		var q_tpose_r := Quaternion(r_arm_rest_y, Vector3(1, 0, 0))

		for src_b: String in BONE_MAP:
			var dst_b: String = BONE_MAP[src_b]
			var idx := skel.find_bone(dst_b)
			if idx >= 0:
				var q_base := skel.get_bone_global_rest(idx).basis.get_rotation_quaternion().normalized()
				# 手臂链应用 T-Pose 校准，彻底消除 A-Pose 45° 下垂初始残差
				if src_b in ["LeftUpperArm", "LeftLowerArm", "LeftHand"]:
					d_gr[src_b] = (q_tpose_l * q_base).normalized()
				elif src_b in ["RightUpperArm", "RightLowerArm", "RightHand"]:
					d_gr[src_b] = (q_tpose_r * q_base).normalized()
				else:
					d_gr[src_b] = q_base

		# 3. 建立 Aster 真实父子关系
		var dst_real_parents := {}
		for i in skel.get_bone_count():
			var bname := skel.get_bone_name(i)
			var p_idx := skel.get_bone_parent(i)
			dst_real_parents[bname] = skel.get_bone_name(p_idx) if p_idx >= 0 else ""

		# 4. 构建测试剪辑
		var out := AnimationLibrary.new()
		for item in [["idle", shooter, "idle", "shooter"], ["LightIdle", melee, "LightIdle", "melee"], ["Slash1", melee, "Slash1", "melee"], ["LightRunning", melee, "LightRunning", "melee"]]:
			var clip_name: String = item[0]
			var lib: AnimationLibrary = item[1]
			var src_name: String = item[2]
			var s_gr: Dictionary = s_gr_dict[item[3]]
			
			if not lib.has_animation(src_name):
				continue
			var src_anim := lib.get_animation(src_name)
			var out_anim := Animation.new()
			out_anim.length = src_anim.length
			out_anim.step = src_anim.step
			out_anim.loop_mode = Animation.LOOP_LINEAR if clip_name != "Slash1" else Animation.LOOP_NONE

			var src_track := {}
			for t in src_anim.get_track_count():
				if src_anim.track_get_type(t) == Animation.TYPE_ROTATION_3D:
					var bname := String(src_anim.track_get_path(t).get_subname(0))
					if BONE_MAP.has(bname):
						src_track[bname] = t

			var order: Array[String] = []
			for pass_i in range(8):
				for b: String in SRC_PARENTS:
					if not src_track.has(b) or b in order:
						continue
					var p: String = SRC_PARENTS[b]
					if p == "" or not src_track.has(p) or p in order:
						order.append(b)
				if order.size() == src_track.size():
					break

			var out_tracks := {}
			for b in order:
				var dst_b: String = BONE_MAP[b]
				var nt := out_anim.add_track(Animation.TYPE_ROTATION_3D)
				out_anim.track_set_path(nt, NodePath("Skeleton3D:%s" % dst_b))
				out_tracks[b] = nt

			var times_set := {}
			for b in order:
				var tb: int = src_track[b]
				for k in src_anim.track_get_key_count(tb):
					times_set[src_anim.track_get_key_time(tb, k)] = true
			var times := times_set.keys()
			times.sort()

			for time: float in times:
				var sg_curr := {}
				for b in order:
					var p: String = SRC_PARENTS[b]
					var p_sg: Quaternion = sg_curr.get(p, Quaternion.IDENTITY)
					var q_local: Quaternion = src_anim.rotation_track_interpolate(src_track[b], time).normalized()
					var sg_b: Quaternion = (p_sg * q_local).normalized()
					sg_curr[b] = sg_b

				var dg_curr := {}
				for b in order:
					var sg_180: Quaternion = (q_rot_180 * sg_curr[b] * q_rot_180.inverse()).normalized()
					var m_b: Quaternion = (d_gr[b] * s_gr[b].inverse()).normalized()
					var dg_b: Quaternion = (m_b * sg_180).normalized()
					dg_curr[BONE_MAP[b]] = dg_b

				if not dg_curr.has("Pelvis") and dg_curr.has("Hip"):
					var idx_p := skel.find_bone("Pelvis")
					var q_pelvis_rest := skel.get_bone_rest(idx_p).basis.get_rotation_quaternion().normalized()
					dg_curr["Pelvis"] = (dg_curr["Hip"] * q_pelvis_rest).normalized()

				for b in order:
					var dst_b: String = BONE_MAP[b]
					var real_parent: String = dst_real_parents.get(dst_b, "")
					var parent_dg: Quaternion = dg_curr.get(real_parent, Quaternion.IDENTITY)
					var q_local: Quaternion = (parent_dg.inverse() * dg_curr[dst_b]).normalized()
					out_anim.rotation_track_insert_key(out_tracks[b], time, q_local)

			out.add_animation(clip_name, out_anim)
			print("PerfectRetarget clip built: ", clip_name)

		return out

	func _physics_process(_delta: float) -> void:
		tick += 1
		var cpos: Vector3 = player.global_position

		# 1. 播放文静优雅待命 idle
		if tick == 10:
			anim_player.play("perf_test/idle")
		elif tick == 25:
			# 全身正面
			cam.global_position = cpos + Vector3(0.0, 0.85, -2.6)
			cam.look_at(cpos + Vector3(0.0, 0.80, 0.0), Vector3.UP)
			cam.make_current()
		elif tick == 30:
			_save(artifact_dir + "/perf_01_idle_front.png")

		elif tick == 35:
			# 双脚微距正面
			cam.global_position = cpos + Vector3(0.0, 0.16, -0.85)
			cam.look_at(cpos + Vector3(0.0, 0.10, 0.0), Vector3.UP)
		elif tick == 40:
			_save(artifact_dir + "/perf_02_idle_feet.png")

		# 2. 播放奔跑 LightRunning
		elif tick == 45:
			anim_player.play("perf_test/LightRunning")
		elif tick == 60:
			# 跑步侧面
			cam.global_position = cpos + Vector3(-2.8, 0.85, 0.0)
			cam.look_at(cpos + Vector3(0.0, 0.80, 0.0), Vector3.UP)
		elif tick == 65:
			_save(artifact_dir + "/perf_03_run_side.png")

		# 3. 播放挥砍 Slash1
		elif tick == 70:
			rig.draw_sword()
			anim_player.play("perf_test/Slash1")
		elif tick == 85:
			# 挥砍正面
			cam.global_position = cpos + Vector3(0.0, 0.85, -2.6)
			cam.look_at(cpos + Vector3(0.0, 0.80, 0.0), Vector3.UP)
		elif tick == 90:
			_save(artifact_dir + "/perf_04_slash1_front.png")
			print("=== PerfectRetarget 全部截图已捕获 ===")
			get_tree().quit(0)

	func _save(path: String) -> void:
		var img := get_viewport().get_texture().get_image()
		if img:
			img.save_png(path)
			print("Saved: ", path)
