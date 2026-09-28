extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(5):
		await process_frame
		
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	rig.set_locomotion_blend(2.4)
	
	# Remove outline passes from all meshes
	for mi in [rig.find_child("Aster_Body", true, false), rig.find_child("Katana_Blade", true, false), rig.find_child("Katana_Scabbard", true, false)]:
		if mi:
			for s in range(mi.mesh.get_surface_count()):
				var mat = mi.get_surface_override_material(s)
				if mat:
					mat.next_pass = null
					
	for i in range(20):
		await physics_frame
		
	var cam: Camera3D = scene.find_child("Camera3D", true, false)
	if cam:
		cam.fov = 40.0
		
	await process_frame
	var img = root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/e2a54378-0bc7-4ac4-812a-63fffb6115fa/inspect_motion/no_outline.png")
	print("Saved no_outline.png!")
	quit()
