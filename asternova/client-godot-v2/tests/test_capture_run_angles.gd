extends SceneTree

func _init() -> void:
	root.size = Vector2i(1920, 1080)
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	for i in range(5):
		await process_frame

	var player = playground.get_node("Player") as PlayerController
	var rig = player.visual_root.get_node("CharacterAster") as AsterRig
	var cam_ctrl = player.camera_controller
	var spring_arm = player.find_child("SpringArm3D", true, false) as SpringArm3D
	
	# Disable cam_ctrl _process so it doesn't fight our camera poses
	cam_ctrl.set_process(false)

	# Set running motion
	player.combat_fsm.change_state(PlayerCombatFSM.State.MOVE)
	player.input_direction = Vector3(0, 0, -1)
	player.velocity = Vector3(0, 0, -6.5)
	rig.set_locomotion_blend(6.5)

	# Run for 20 frames to let running animation stabilize
	for i in range(25):
		player.input_direction = Vector3(0, 0, -1)
		player.velocity = Vector3(0, 0, -6.5)
		rig.set_locomotion_blend(6.5)
		await physics_frame

	# 1. Profile Right Side View
	spring_arm.position = Vector3(0, 0.85, 0)
	spring_arm.rotation_degrees = Vector3(-2, 90, 0)
	spring_arm.spring_length = 2.4
	for i in range(5):
		await physics_frame
	await RenderingServer.frame_post_draw
	var img = root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/test_run_profile_right.png")
	print("Saved test_run_profile_right.png")

	# 2. Profile Left Side View
	spring_arm.rotation_degrees = Vector3(-2, -90, 0)
	for i in range(5):
		await physics_frame
	await RenderingServer.frame_post_draw
	img = root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/test_run_profile_left.png")
	print("Saved test_run_profile_left.png")

	# 3. Behind View while running
	spring_arm.rotation_degrees = Vector3(-5, 0, 0)
	spring_arm.spring_length = 2.2
	for i in range(5):
		await physics_frame
	await RenderingServer.frame_post_draw
	img = root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/test_run_chase_back.png")
	print("Saved test_run_chase_back.png")

	quit(0)
