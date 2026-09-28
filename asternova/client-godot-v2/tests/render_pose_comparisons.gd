extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	var runner = PoseComparisonCapturer.new()
	playground.add_child(runner)

class PoseComparisonCapturer extends Node:
	var tick: int = 0
	var player: PlayerController = null
	var rig: AsterRig = null
	var cam_ctrl: CameraController = null
	var artifact_dir := "C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165"

	func _ready() -> void:
		var scene_root := get_parent()
		player = scene_root.get_node_or_null("Player") as PlayerController
		rig = player.visual_root.get_node_or_null("CharacterAster") as AsterRig
		cam_ctrl = player.camera_controller

	func _set_camera(yaw_deg: float, pitch_deg: float, dist: float, offset_y: float = 0.85, offset_x: float = 0.0) -> void:
		if not cam_ctrl:
			return
		cam_ctrl.current_yaw = deg_to_rad(yaw_deg)
		cam_ctrl.current_pitch = deg_to_rad(pitch_deg)
		cam_ctrl.rotation.y = cam_ctrl.current_yaw
		cam_ctrl.target_arm_offset = Vector3(offset_x, offset_y, 0.0)
		cam_ctrl.current_arm_offset = cam_ctrl.target_arm_offset
		cam_ctrl.target_arm_length = dist
		cam_ctrl.spring_arm.position = cam_ctrl.target_arm_offset
		cam_ctrl.spring_arm.spring_length = dist
		cam_ctrl.spring_arm.rotation = Vector3(cam_ctrl.current_pitch, 0.0, 0.0)

	func _physics_process(_delta: float) -> void:
		tick += 1
		
		# Test 1: Rest Pose (No Animation)
		if tick == 10:
			rig.anim_tree.active = false
			rig.anim_player.stop()
			rig.skeleton.reset_bone_poses()
			# Look directly at feet from front: height 0.15m, pitch -5 deg (looking slightly down), dist 0.8m
			_set_camera(180.0, -5.0, 0.8, 0.15)
		elif tick == 15:
			_save_frame(artifact_dir + "/test_rest_feet_closeup.png")

		elif tick == 20:
			# Rest Pose full body front
			_set_camera(180.0, -2.0, 2.2, 0.85)
		elif tick == 25:
			_save_frame(artifact_dir + "/test_rest_fullbody_front.png")

		# Test 2: ShooterLib "idle"
		elif tick == 30:
			rig.anim_tree.active = false
			rig.anim_player.play("idle")
			_set_camera(180.0, -2.0, 2.2, 0.85)
		elif tick == 45:
			_save_frame(artifact_dir + "/test_shooter_idle_fullbody.png")

		# Test 3: MeleeLib "LightIdle" (Current default)
		elif tick == 50:
			rig.anim_tree.active = false
			rig.anim_player.play("LightIdle")
			_set_camera(180.0, -2.0, 2.2, 0.85)
		elif tick == 65:
			_save_frame(artifact_dir + "/test_melee_lightidle_fullbody.png")

		elif tick == 70:
			# Look at feet under LightIdle
			_set_camera(180.0, -5.0, 0.8, 0.15)
		elif tick == 75:
			_save_frame(artifact_dir + "/test_melee_lightidle_feet.png")
			get_tree().quit(0)

	func _save_frame(path: String) -> void:
		var img := get_viewport().get_texture().get_image()
		if img:
			var err := img.save_png(path)
			print("Saved [err=", err, "]: ", path)
