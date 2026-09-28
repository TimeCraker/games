extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	var capturer = CleanPlaygroundCapturer.new()
	capturer.name = "CleanPlaygroundCapturer"
	playground.add_child(capturer)

class CleanPlaygroundCapturer extends Node:
	var tick: int = 0
	var player: PlayerController = null
	var rig: AsterRig = null
	var custom_cam: Camera3D = null
	var artifact_dir := "C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165"

	func _ready() -> void:
		var scene_root := get_parent()
		player = scene_root.get_node_or_null("Player") as PlayerController
		rig = player.visual_root.get_node_or_null("CharacterAster") as AsterRig
		
		custom_cam = Camera3D.new()
		custom_cam.name = "VerifiedReviewCam"
		add_child(custom_cam)

	func _set_cam(pos: Vector3, look_at_target: Vector3) -> void:
		custom_cam.global_position = pos
		custom_cam.look_at(look_at_target, Vector3.UP)
		custom_cam.make_current()

	func _physics_process(_delta: float) -> void:
		tick += 1
		var cpos: Vector3 = player.global_position

		# 1. 待命：超近景双脚与玛丽珍鞋正视角特写（相机平视鞋面，细致展现搭扣、蝴蝶结、花边袜口与鞋跟）
		if tick == 12:
			_set_cam(cpos + Vector3(0.0, 0.12, -0.42), cpos + Vector3(0.0, 0.07, 0.0))
		elif tick == 18:
			_save_frame(artifact_dir + "/v3_verified_01_shoes_closeup.png")

		# 2. 待命：正面全身立绘（平视全身：自然收拢双手、挺拔修长双腿、端庄优雅体态）
		elif tick == 22:
			_set_cam(cpos + Vector3(0.0, 0.85, -2.25), cpos + Vector3(0.0, 0.82, 0.0))
		elif tick == 30:
			_save_frame(artifact_dir + "/v3_verified_02_idle_front.png")

		# 3. 待命：背后立绘（观察长发瀑布、后背层次、后裙摆、左腰鞘佩刀与双跟接地）
		elif tick == 34:
			_set_cam(cpos + Vector3(0.0, 0.85, 2.25), cpos + Vector3(0.0, 0.82, 0.0))
		elif tick == 42:
			_save_frame(artifact_dir + "/v3_verified_03_idle_back.png")

		# 4. 奔跑动力学状态
		elif tick == 45:
			player.combat_fsm.change_state(PlayerCombatFSM.State.MOVE)
			player.input_direction = Vector3(0, 0, -1)
			player.velocity = Vector3(0, 0, -6.5)
			rig.set_locomotion_blend(6.5)
		elif tick == 65:
			# 奔跑侧身视角（观察大跨步冲刺、双腿自然迈步解耦、零跨腿肉膜拉扯）
			_set_cam(cpos + Vector3(-2.2, 0.80, 0.0), cpos + Vector3(0.0, 0.75, 0.0))
		elif tick == 75:
			_save_frame(artifact_dir + "/v3_verified_04_run_side.png")

		# 5. 战斗挥砍姿态 (Slash1)
		elif tick == 80:
			player.input_direction = Vector3.ZERO
			player.velocity = Vector3.ZERO
			rig.draw_sword()
			rig.travel("Combo1")
		elif tick == 92:
			# 挥砍姿态（正面微斜，展现拔刀挥刃轨迹与英姿飒爽下肢发力支撑）
			_set_cam(cpos + Vector3(-1.4, 0.85, -1.8), cpos + Vector3(0.0, 0.80, 0.0))
		elif tick == 100:
			_save_frame(artifact_dir + "/v3_verified_05_slash_draw.png")
			print("=== 全部 5 张真实 GPU 渲染核验截图保存完成 ===")
			get_tree().quit(0)

	func _save_frame(path: String) -> void:
		var img := get_viewport().get_texture().get_image()
		if img:
			var err := img.save_png(path)
			print("Saved [err=", err, "]: ", path)
