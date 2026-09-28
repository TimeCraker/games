extends SceneTree

func _init() -> void:
	root.size = Vector2i(1920, 1080)
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	for i in range(5):
		await process_frame

	var player = playground.get_node("Player") as PlayerController
	var rig = player.visual_root.get_node("CharacterAster") as AsterRig
	var spring_arm = player.find_child("SpringArm3D", true, false) as SpringArm3D

	# Tune WorldEnvironment
	var env_node = playground.get_node_or_null("WorldEnvironment") as WorldEnvironment
	if env_node and env_node.environment:
		env_node.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env_node.environment.ambient_light_color = Color(0.6, 0.65, 0.75)
		env_node.environment.ambient_light_energy = 0.5

	# Set pure white albedo_color
	var body = rig.find_child("Aster_Body", true, false) as MeshInstance3D
	if body:
		var mat = body.get_surface_override_material(0) as ShaderMaterial
		if mat:
			mat.set_shader_parameter("albedo_color", Color(1.0, 1.0, 1.0, 1.0))
			mat.set_shader_parameter("shadow_tint", Color(0.72, 0.75, 0.88, 1.0))
			mat.set_shader_parameter("shadow_strength", 0.40)
			mat.set_shader_parameter("ramp_threshold", 0.46)
			mat.set_shader_parameter("ramp_smoothness", 0.04)

	# 1. Close-up Portrait
	if spring_arm:
		spring_arm.position = Vector3(0, 1.35, 0)
		spring_arm.rotation_degrees = Vector3(-2, 180, 0)
		spring_arm.spring_length = 0.95

	for i in range(15):
		await physics_frame
	await RenderingServer.frame_post_draw
	var img = root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/test_portrait_close.png")
	print("Saved test_portrait_close.png")

	# 2. Full Body Front
	if spring_arm:
		spring_arm.position = Vector3(0, 0.85, 0)
		spring_arm.rotation_degrees = Vector3(-4, 180, 0)
		spring_arm.spring_length = 2.2
	for i in range(15):
		await physics_frame
	await RenderingServer.frame_post_draw
	img = root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/test_fullbody_front.png")
	print("Saved test_fullbody_front.png")

	# 3. Full Body Back (Scabbard & Hair)
	if spring_arm:
		spring_arm.position = Vector3(0, 0.85, 0)
		spring_arm.rotation_degrees = Vector3(-4, 0, 0)
		spring_arm.spring_length = 2.2
	for i in range(15):
		await physics_frame
	await RenderingServer.frame_post_draw
	img = root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/test_fullbody_back.png")
	print("Saved test_fullbody_back.png")

	quit(0)
