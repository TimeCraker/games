extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var scene = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(scene)
	
	var runner = Runner.new()
	scene.add_child(runner)

class Runner extends Node:
	var tick: int = 0
	func _physics_process(_delta: float) -> void:
		tick += 1
		if tick == 1:
			var player = get_parent().get_node_or_null("Player") as PlayerController
			var rig = player.visual_root.get_node_or_null("CharacterAster") as AsterRig
			rig.scale = Vector3(1.65, 1.65, 1.65)
			
			# 还原 Aster_Body 原厂材质！
			var body = rig.find_child("Aster_Body", true, false) as MeshInstance3D
			if body:
				body.set_surface_override_material(0, null)
				
			var spring = player.find_child("SpringArm3D", true, false) as SpringArm3D
			if spring:
				spring.position = Vector3(0, 0.9, 0)
				spring.rotation_degrees = Vector3(-6, 175, 0)
				spring.spring_length = 2.8
		elif tick == 40:
			_capture()
			
	func _capture() -> void:
		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/test_orig_mat_in_game.png")
		print("保存成功: test_orig_mat_in_game.png")
		get_tree().quit(0)
