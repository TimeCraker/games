extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(5):
		await process_frame
		
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	var cam: Camera3D = scene.find_child("Camera3D", true, false)
	var spring: SpringArm3D = scene.find_child("SpringArm3D", true, false)
	
	# Position camera to the exact side (X = +2.5, Y = 1.0, Z = 0.0) looking at Aster
	if spring:
		spring.position = Vector3(0, 0.8, 0)
		spring.rotation_degrees = Vector3(0, 90, 0) # side view
		spring.spring_length = 2.5
		
	# Test 1: Walk (blend = 2.0)
	rig.set_locomotion_blend(2.0)
	for f in range(15):
		await physics_frame
	var img_walk = root.get_viewport().get_texture().get_image()
	img_walk.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/e2a54378-0bc7-4ac4-812a-63fffb6115fa/inspect_motion/side_walk.png")
	
	# Test 2: Jog/Run (blend = 4.5)
	rig.set_locomotion_blend(4.5)
	for f in range(15):
		await physics_frame
	var img_jog = root.get_viewport().get_texture().get_image()
	img_jog.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/e2a54378-0bc7-4ac4-812a-63fffb6115fa/inspect_motion/side_jog.png")
	
	print("Saved side_walk.png and side_jog.png!")
	quit()
