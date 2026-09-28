extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	var capturer = ActionDiagnosisCapturer.new()
	capturer.name = "ActionDiagnosisCapturer"
	playground.add_child(capturer)

class ActionDiagnosisCapturer extends Node:
	var tick: int = 0
	var player: PlayerController = null
	var rig: AsterRig = null
	var cam: Camera3D = null
	var artifact_dir := "C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165"

	func _ready() -> void:
		var scene_root := get_parent()
		player = scene_root.get_node_or_null("Player") as PlayerController
		rig = player.visual_root.get_node_or_null("CharacterAster") as AsterRig
		
		cam = Camera3D.new()
		cam.name = "DiagCam"
		cam.fov = 38.0  # 中长焦防透视畸变
		add_child(cam)

	func _set_cam(pos: Vector3, target: Vector3) -> void:
		cam.global_position = pos
		cam.look_at(target, Vector3.UP)
		cam.make_current()

	func _physics_process(_delta: float) -> void:
		tick += 1
		var cpos: Vector3 = player.global_position

		# 等待 20 帧让物理完全落地稳定
		if tick == 25:
			# 1. 待命 IDLE：双脚微距正面平视
			_set_cam(cpos + Vector3(0.0, 0.16, -0.85), cpos + Vector3(0.0, 0.10, 0.0))
		elif tick == 30:
			_save_frame(artifact_dir + "/diag_01_idle_feet_front.png")

		elif tick == 35:
			# 2. 待命 IDLE：双脚微距背面
			_set_cam(cpos + Vector3(0.0, 0.16, 0.85), cpos + Vector3(0.0, 0.10, 0.0))
		elif tick == 40:
			_save_frame(artifact_dir + "/diag_02_idle_feet_back.png")

		elif tick == 45:
			# 3. 待命 IDLE：全身正面
			_set_cam(cpos + Vector3(0.0, 0.85, -2.6), cpos + Vector3(0.0, 0.80, 0.0))
		elif tick == 50:
			_save_frame(artifact_dir + "/diag_03_idle_full_front.png")

		elif tick == 55:
			# 4. 待命 IDLE：全身侧面
			_set_cam(cpos + Vector3(-2.6, 0.85, 0.0), cpos + Vector3(0.0, 0.80, 0.0))
		elif tick == 60:
			_save_frame(artifact_dir + "/diag_04_idle_full_side.png")

		# 切换到奔跑状态
		elif tick == 65:
			player.combat_fsm.change_state(PlayerCombatFSM.State.MOVE)
			player.input_direction = Vector3(0, 0, -1)
			player.velocity = Vector3(0, 0, -7.0)
			rig.set_locomotion_blend(7.0)
		elif tick == 80:
			# 5. 奔跑 RUN：全身侧面迈步
			_set_cam(cpos + Vector3(-2.8, 0.85, 0.0), cpos + Vector3(0.0, 0.80, 0.0))
		elif tick == 85:
			_save_frame(artifact_dir + "/diag_05_run_full_side.png")

		elif tick == 90:
			# 6. 奔跑 RUN：全身正面
			_set_cam(cpos + Vector3(0.0, 0.85, -2.8), cpos + Vector3(0.0, 0.80, 0.0))
		elif tick == 95:
			_save_frame(artifact_dir + "/diag_06_run_full_front.png")

		# 触发斩击
		elif tick == 100:
			player.input_direction = Vector3.ZERO
			player.velocity = Vector3.ZERO
			rig.draw_sword()
			rig.travel("Combo1")
		elif tick == 112:
			# 7. 挥刀斩击：全身正面
			_set_cam(cpos + Vector3(0.0, 0.85, -2.6), cpos + Vector3(0.0, 0.80, 0.0))
		elif tick == 115:
			_save_frame(artifact_dir + "/diag_07_slash1_full_front.png")

		elif tick == 120:
			print("=== 诊断截图已全部捕获 ===")
			get_tree().quit(0)

	func _save_frame(path: String) -> void:
		var img := get_viewport().get_texture().get_image()
		if img:
			var err := img.save_png(path)
			print("Saved: ", path, " err=", err)
