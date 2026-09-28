extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	# Wait for ready
	for i in range(5):
		await process_frame
	
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	# Simulate walk speed 2.4 m/s (same as user screenshot)
	rig.set_locomotion_blend(2.4)
	
	for i in range(20):
		await physics_frame
		
	# Take a viewport screenshot from side and back
	var img = root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/e2a54378-0bc7-4ac4-812a-63fffb6115fa/inspect_motion/godot_runtime_screenshot.png")
	print("Saved godot_runtime_screenshot.png!")
	quit()
