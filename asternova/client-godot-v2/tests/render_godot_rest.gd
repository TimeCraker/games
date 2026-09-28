extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1000, 1000)
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node3D = scene.instantiate()
	root.add_child(inst)
	
	# 添加相机从侧面看
	var cam := Camera3D.new()
	root.add_child(cam)
	cam.position = Vector3(2.2, 0.85, 0.0) # 侧面看
	cam.rotation_degrees = Vector3(0, 90, 0)
	cam.current = true
	
	# 添加灯光
	var light := DirectionalLight3D.new()
	root.add_child(light)
	light.rotation_degrees = Vector3(-30, 45, 0)
	
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/scratch/godot_rest_side.png")
	
	# 从正面看
	cam.position = Vector3(0.0, 0.85, -2.2) # 正面看 (-Z)
	cam.rotation_degrees = Vector3(0, 180, 0)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	img = root.get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/scratch/godot_rest_front.png")
	
	print("GODOT_REST_RENDER_DONE")
	quit(0)
