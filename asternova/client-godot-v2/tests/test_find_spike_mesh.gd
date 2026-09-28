extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(5):
		await process_frame
		
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	var cam: Camera3D = scene.find_child("Camera3D", true, false)
	var spring: SpringArm3D = scene.find_child("SpringArm3D", true, false)
	if spring:
		spring.position = Vector3(0, 0.8, 0)
		spring.rotation_degrees = Vector3(0, 90, 0)
		spring.spring_length = 2.5
		
	rig.set_locomotion_blend(2.0)
	for f in range(15):
		await physics_frame
		
	# Test A: Hide Katana_Blade
	var kb = rig.find_child("Katana_Blade", true, false)
	var ks = rig.find_child("Katana_Scabbard", true, false)
	var body = rig.find_child("Aster_Body", true, false)
	
	kb.visible = false
	ks.visible = false
	await process_frame
	var img_body_only = root.get_viewport().get_texture().get_image()
	img_body_only.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/e2a54378-0bc7-4ac4-812a-63fffb6115fa/inspect_motion/spike_body_only.png")
	
	# Test B: Hide Body, Show Katana
	kb.visible = true
	ks.visible = true
	body.visible = false
	await process_frame
	var img_katana_only = root.get_viewport().get_texture().get_image()
	img_katana_only.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/e2a54378-0bc7-4ac4-812a-63fffb6115fa/inspect_motion/spike_katana_only.png")
	
	print("Saved spike_body_only.png and spike_katana_only.png")
	quit()
