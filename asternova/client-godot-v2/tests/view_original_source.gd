extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var glb_path := "c:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/models/source/aster_tripo_39caf44b/aster_source.glb"
	var gltf := GLTFDocument.new()
	var state := GLTFState.new()
	var err := gltf.append_from_file(glb_path, state)
	var char_root := gltf.generate_scene(state)
	root.add_child(char_root)

	var cam := Camera3D.new()
	root.add_child(cam)
	cam.position = Vector3(0, 0.55, 1.3)
	cam.look_at_from_position(Vector3(0, 0.55, 1.3), Vector3(0, 0.55, 0), Vector3.UP)
	cam.make_current()

	var light := DirectionalLight3D.new()
	root.add_child(light)
	light.position = Vector3(1, 2, 2)
	light.look_at_from_position(Vector3(1, 2, 2), Vector3(0, 0.55, 0), Vector3.UP)
	light.light_energy = 0.9

	for i in range(15):
		await process_frame

	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/view_original_source_glb.png")
	print("已保存原厂源模真实渲染: view_original_source_glb.png")
	quit(0)
