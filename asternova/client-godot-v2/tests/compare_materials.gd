extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var path := "res://scenes/entities/character_aster.tscn"
	var char_aster: AsterRig = load(path).instantiate() as AsterRig
	root.add_child(char_aster)

	# 恢复原厂材质（清空 override）
	var body: MeshInstance3D = char_aster.find_child("Aster_Body", true, false) as MeshInstance3D
	if body:
		body.set_surface_override_material(0, null)
	
	# 把佩刀也暂时隐藏或设原厂
	var blade = char_aster.find_child("Katana_Blade", true, false) as MeshInstance3D
	if blade:
		for s in blade.mesh.get_surface_count():
			blade.set_surface_override_material(s, null)
	var scabbard = char_aster.find_child("Katana_Scabbard", true, false) as MeshInstance3D
	if scabbard:
		for s in scabbard.mesh.get_surface_count():
			scabbard.set_surface_override_material(s, null)

	var cam := Camera3D.new()
	root.add_child(cam)
	cam.position = Vector3(0, 0.85, 1.8)
	cam.look_at(Vector3(0, 0.85, 0), Vector3.UP)
	cam.make_current()

	var light := DirectionalLight3D.new()
	root.add_child(light)
	light.position = Vector3(1, 2, 2)
	light.look_at(Vector3(0, 0.85, 0), Vector3.UP)
	light.light_energy = 1.0

	for i in range(15):
		await process_frame

	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165/inspect_char_standard_mat.png")
	print("已保存原厂材质特写: inspect_char_standard_mat.png")
	quit(0)
