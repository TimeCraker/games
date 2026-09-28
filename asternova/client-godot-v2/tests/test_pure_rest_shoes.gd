extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	var capturer = RestShoesCapturer.new()
	capturer.name = "RestShoesCapturer"
	playground.add_child(capturer)

class RestShoesCapturer extends Node:
	var tick: int = 0
	var player: PlayerController = null
	var rig: AsterRig = null
	var skel: Skeleton3D = null
	var cam: Camera3D = null
	var artifact_dir := "C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165"

	func _ready() -> void:
		var scene_root := get_parent()
		player = scene_root.get_node_or_null("Player") as PlayerController
		rig = player.visual_root.get_node_or_null("CharacterAster") as AsterRig
		
		# 彻底禁用动画驱动，完全恢复原生 Rest 姿态
		if rig.anim_tree:
			rig.anim_tree.active = false
		if rig.anim_player:
			rig.anim_player.stop()
		
		skel = rig.find_child("Skeleton3D", true, false) as Skeleton3D
		if skel:
			skel.reset_bone_poses()
			print("Skeleton reset to REST successfully!")
		
		cam = Camera3D.new()
		cam.fov = 32.0  # 高清微距无畸变
		add_child(cam)

	func _physics_process(_delta: float) -> void:
		tick += 1
		var cpos: Vector3 = player.global_position
		if skel:
			skel.reset_bone_poses()  # 确保每帧都是纯净 Rest

		if tick == 10:
			# 正面平视双脚
			cam.global_position = cpos + Vector3(0.0, 0.14, -0.9)
			cam.look_at(cpos + Vector3(0.0, 0.08, 0.0), Vector3.UP)
			cam.make_current()
		elif tick == 15:
			_save(artifact_dir + "/pure_rest_01_feet_front.png")

		elif tick == 20:
			# 右脚单脚特写（也就是之前有纵向黑线的脚）
			cam.global_position = cpos + Vector3(-0.06, 0.12, -0.6)
			cam.look_at(cpos + Vector3(-0.05, 0.06, 0.0), Vector3.UP)
		elif tick == 25:
			_save(artifact_dir + "/pure_rest_02_r_foot_closeup.png")

		elif tick == 30:
			# 左脚单脚特写（之前鞋底有横向黑线的脚）
			cam.global_position = cpos + Vector3(0.06, 0.12, -0.6)
			cam.look_at(cpos + Vector3(0.05, 0.06, 0.0), Vector3.UP)
		elif tick == 35:
			_save(artifact_dir + "/pure_rest_03_l_foot_closeup.png")

		elif tick == 40:
			# 背面平视双脚后跟
			cam.global_position = cpos + Vector3(0.0, 0.14, 0.9)
			cam.look_at(cpos + Vector3(0.0, 0.08, 0.0), Vector3.UP)
		elif tick == 45:
			_save(artifact_dir + "/pure_rest_04_feet_back.png")
			get_tree().quit(0)

	func _save(path: String) -> void:
		var img := get_viewport().get_texture().get_image()
		if img:
			img.save_png(path)
			print("Saved: ", path)
