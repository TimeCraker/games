extends Node3D

const SAMPLE = preload("res://models/characters/rework/white_static.glb")
const BASELINE = preload("res://models/characters/white.glb")
var sample: Node3D
var baseline: Node3D
var camera: Camera3D
var status: Label
var baseline_player: AnimationPlayer
var baseline_skeleton: Skeleton3D
var yaw := 0.0
var pitch := 0.0
var zoom := 2.0
var head_view := false
var turning := false
var mode := 1
var clay := false
var toon := true
var clay_material := StandardMaterial3D.new()

func _ready() -> void:
	sample = SAMPLE.instantiate()
	baseline = BASELINE.instantiate()
	add_child(sample)
	add_child(baseline)
	_prepare_review_materials(sample)
	_set_toon(sample)
	baseline_player = _find_type(baseline, "AnimationPlayer") as AnimationPlayer
	baseline_skeleton = _find_type(baseline, "Skeleton3D") as Skeleton3D
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.11, 0.14, 0.20)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.80, 0.86, 1.0)
	environment.ambient_light_energy = 0.45
	environment.tonemap_mode = Environment.TONE_MAPPER_AGX
	var world := WorldEnvironment.new()
	world.environment = environment
	add_child(world)
	for entry in [[Vector3(-30, -30, 0), 1.2, Color(1.0, 0.98, 0.95)], [Vector3(-15, 145, 0), 0.55, Color(0.78, 0.86, 1.0)]]:
		var light := DirectionalLight3D.new()
		light.rotation_degrees = entry[0]
		light.light_energy = entry[1]
		light.light_color = entry[2]
		add_child(light)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	add_child(camera)
	camera.make_current()
	get_viewport().msaa_3d = Viewport.MSAA_4X
	clay_material.albedo_color = Color(0.72, 0.75, 0.79)
	clay_material.roughness = 0.85
	_build_ui()
	_set_mode(1)
	_update_camera()
	if "--verify-white-static" in OS.get_cmdline_user_args():
		_verify()

func _find_type(root: Node, type_name: String) -> Node:
	if root.is_class(type_name):
		return root
	for child in root.get_children():
		var found := _find_type(child, type_name)
		if found:
			return found
	return null

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := PanelContainer.new()
	panel.position = Vector2(24, 24)
	layer.add_child(panel)
	var column := VBoxContainer.new()
	panel.add_child(column)
	var title := Label.new()
	title.text = "白色静态样板 · 待用户确认"
	title.add_theme_font_size_override("font_size", 24)
	column.add_child(title)
	status = Label.new()
	column.add_child(status)
	var help := Label.new()
	help.text = "1 当前样板  /  2 旧版休止  /  3 旧版 Idle\nV 正侧背  ·  H 头部  ·  M 素模  ·  P 转台\nN 切换 Toon/PBR  ·  右键环绕  ·  滚轮缩放"
	column.add_child(help)

func _set_mode(value: int) -> void:
	mode = value
	sample.visible = mode == 1
	baseline.visible = mode != 1
	if baseline_player:
		baseline_player.stop()
	if baseline_skeleton:
		baseline_skeleton.reset_bone_poses()
	if mode == 3 and baseline_player and baseline_player.has_animation("Idle"):
		baseline_player.play("Idle")
		baseline_player.seek(0.0, true)
	status.text = ["", "当前：静态外观待确认，尚未绑定", "旧版：休止姿态", "旧版：Idle 动作"][mode]

func _update_camera() -> void:
	var target := Vector3(0, 1.53 if head_view else 0.88, 0)
	camera.size = zoom * (0.27 if head_view else 1.0)
	camera.position = target + Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch)) * 5.0
	camera.look_at(target)

func _process(delta: float) -> void:
	if turning:
		yaw += delta * 0.35
		_update_camera()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
		yaw -= event.relative.x * 0.006
		pitch = clampf(pitch + event.relative.y * 0.004, -0.7, 0.7)
		_update_camera()
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom = maxf(0.8, zoom * 0.9)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom = minf(3.5, zoom * 1.1)
		_update_camera()
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_1: _set_mode(1)
			KEY_2: _set_mode(2)
			KEY_3: _set_mode(3)
			KEY_V:
				yaw += PI / 2.0
				pitch = 0.0
				_update_camera()
			KEY_H:
				head_view = not head_view
				_update_camera()
			KEY_P: turning = not turning
			KEY_N:
				toon = not toon
				_set_toon(sample)
			KEY_M:
				clay = not clay
				_set_clay(sample)
				_set_clay(baseline)

func _set_clay(node: Node) -> void:
	if node is MeshInstance3D:
		node.material_override = clay_material if clay else null
	for child in node.get_children():
		_set_clay(child)

func _prepare_review_materials(node: Node) -> void:
	if node is MeshInstance3D:
		var pairs: Array[Dictionary] = []
		for index in node.mesh.get_surface_count():
			var original := node.get_active_material(index) as StandardMaterial3D
			if original == null:
				pairs.append({"original": null, "toon": null})
				continue
			var stylized := original.duplicate() as StandardMaterial3D
			stylized.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
			stylized.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
			stylized.emission_enabled = false
			# Flat face lighting is a review option; the source's painted features remain.
			# This is not an SDF face shader or a replacement for face texture repair.
			if String(node.name).begins_with("Head_Work"):
				stylized.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			pairs.append({"original": original, "toon": stylized})
		node.set_meta("review_materials", pairs)
	for child in node.get_children():
		_prepare_review_materials(child)

func _set_toon(node: Node) -> void:
	if node is MeshInstance3D and node.has_meta("review_materials"):
		var pairs: Array = node.get_meta("review_materials")
		for index in pairs.size():
			node.set_surface_override_material(index, pairs[index]["toon" if toon else "original"])
	for child in node.get_children():
		_set_toon(child)

func _verify() -> void:
	var directory := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--evidence="):
			directory = arg.trim_prefix("--evidence=")
	if directory.is_empty():
		push_error("Missing --evidence directory")
		get_tree().quit(2)
		return
	DirAccess.make_dir_recursive_absolute(directory)
	var images: Array[Dictionary] = []
	for setting in [["new_front", 1, 0.0, false, false, true], ["new_left", 1, PI / 2, false, false, true], ["new_back", 1, PI, false, false, true], ["new_right", 1, -PI / 2, false, false, true], ["new_head", 1, 0.0, true, false, true], ["new_clay", 1, 0.0, false, true, true], ["new_front_pbr", 1, 0.0, false, false, false], ["new_head_pbr", 1, 0.0, true, false, false], ["old_rest", 2, 0.0, false, false, false], ["old_idle", 3, 0.0, false, false, false]]:
		_set_mode(setting[1])
		yaw = setting[2]
		head_view = setting[3]
		clay = setting[4]
		toon = setting[5]
		_set_toon(sample)
		_set_clay(sample)
		_set_clay(baseline)
		_update_camera()
		await get_tree().create_timer(0.5).timeout
		await RenderingServer.frame_post_draw
		var code := get_viewport().get_texture().get_image().save_png(directory.path_join(setting[0] + ".png"))
		images.append({"name": setting[0], "save_error": code, "mode": mode, "head": head_view, "clay": clay, "toon": toon})
	var report := {"engine": Engine.get_version_info().string, "renderer": RenderingServer.get_current_rendering_method(), "sample_meshes": _mesh_count(sample), "images": images, "art_approved": false}
	var file := FileAccess.open(directory.path_join("static_report.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	get_tree().quit()

func _mesh_count(node: Node) -> int:
	var count := 1 if node is MeshInstance3D else 0
	for child in node.get_children():
		count += _mesh_count(child)
	return count
