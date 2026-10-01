extends Node3D
## Three modular characters, exported skins and baked CC0 animations.
## Runs inside the main client project with real CharacterBody3D movement.

const CHARACTERS := ["white", "orange", "purple"]
const LABELS := ["白色", "橙色", "紫色"]
const LOOP_CLIPS := ["Idle", "Walk", "Run", "Sprint", "Fall", "Talk"]
const WALK_SPEED := 1.03
const RUN_SPEED := 5.5
var actors: Array[CharacterBody3D] = []
var models: Array[Node3D] = []
var players: Array[AnimationPlayer] = []
var selected := 0
var camera: Camera3D
var status: Label
var yaw := 0.0
var pitch := -0.08
var distance := 4.6
var action_remaining := 0.0
var current_clip := "Idle"
var toon_enabled := false
var original_materials: Dictionary = {}
var verify := false
var elapsed := 0.0
var verify_step := -1
var initial_position := Vector3.ZERO
var max_jump_height := 0.0
var checks: Dictionary = {}
var evidence_path := ""
var selected_start := Vector3.ZERO

func _ready() -> void:
	get_viewport().msaa_3d = Viewport.MSAA_4X
	verify = "--verify-characters" in OS.get_cmdline_user_args()
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--evidence="):
			evidence_path = argument.trim_prefix("--evidence=")
	_make_stage()
	for index in CHARACTERS.size():
		_add_actor(index)
	_make_ui()
	_select(0 if verify else 1)
	if verify:
		DirAccess.make_dir_recursive_absolute(evidence_path)
		initial_position = actors[0].position
		checks["characters"] = []
		for index in actors.size():
			var skeleton := models[index].find_child("Skeleton3D", true, false) as Skeleton3D
			var required := ["Idle", "Walk", "Run", "Sprint", "Jump", "Fall", "Land", "Attack", "Talk"]
			var missing: Array[String] = []
			for clip in required:
				if not players[index].has_animation(clip):
					missing.append(clip)
			checks["characters"].append({"name": CHARACTERS[index], "bones": skeleton.get_bone_count() if skeleton else 0, "missing_clips": missing})

func _make_stage() -> void:
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("172231")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("c0cee8")
	environment.ambient_light_energy = 0.8
	environment.tonemap_mode = Environment.TONE_MAPPER_AGX
	environment.ssao_enabled = true
	world.environment = environment
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-40, -28, 0)
	sun.light_energy = 1.6
	sun.shadow_enabled = true
	add_child(sun)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-20, 145, 0)
	fill.light_color = Color("afcaff")
	fill.light_energy = 0.7
	add_child(fill)
	var floor_body := StaticBody3D.new()
	var floor_mesh := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(40, 40)
	floor_mesh.mesh = plane
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("465469")
	material.roughness = 0.78
	floor_mesh.material_override = material
	floor_body.add_child(floor_mesh)
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(40, 0.2, 40)
	collision.shape = shape
	collision.position.y = -0.1
	floor_body.add_child(collision)
	add_child(floor_body)
	for i in range(-10, 11):
		for axis in 2:
			var line := MeshInstance3D.new()
			var box := BoxMesh.new()
			box.size = Vector3(20, 0.002, 0.015) if axis == 0 else Vector3(0.015, 0.002, 20)
			line.mesh = box
			line.position = Vector3(0, 0.002, i) if axis == 0 else Vector3(i, 0.002, 0)
			var line_material := StandardMaterial3D.new()
			line_material.albedo_color = Color("69768a")
			line.material_override = line_material
			add_child(line)
	camera = Camera3D.new()
	camera.fov = 40
	add_child(camera)
	camera.current = true

func _add_actor(index: int) -> void:
	var body := CharacterBody3D.new()
	body.name = CHARACTERS[index].capitalize()
	body.position.x = (index - 1) * 1.6
	var collider := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.height = 1.65
	capsule.radius = 0.23
	collider.shape = capsule
	collider.position.y = 0.825
	body.add_child(collider)
	var scene := load("res://models/characters/%s.glb" % CHARACTERS[index]) as PackedScene
	assert(scene != null, "Character GLB missing")
	var model := scene.instantiate() as Node3D
	body.add_child(model)
	add_child(body)
	var player := model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	assert(player != null, "AnimationPlayer missing")
	for clip in LOOP_CLIPS:
		if player.has_animation(clip):
			player.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
	player.play("Idle")
	actors.append(body)
	models.append(model)
	players.append(player)

func _make_ui() -> void:
	var canvas := CanvasLayer.new()
	add_child(canvas)
	var panel := PanelContainer.new()
	panel.position = Vector2(24, 24)
	canvas.add_child(panel)
	var label := Label.new()
	label.text = "ASTERNOVA / 角色动作实验场\n1 / 2 / 3 切换角色 · WASD 移动 · Shift 疾跑\n空格 跳跃 · 左键 攻击 · E 展示动作\n右键拖动 环绕 · 滚轮 缩放 · T 材质对比 · R 复位"
	label.add_theme_font_size_override("font_size", 20)
	panel.add_child(label)
	status = Label.new()
	status.position = Vector2(24, 154)
	status.add_theme_font_size_override("font_size", 20)
	canvas.add_child(status)

func _select(index: int) -> void:
	if not players.is_empty():
		players[selected].play("Idle", 0.15)
	selected = index
	current_clip = "Idle"
	action_remaining = 0.0
	players[selected].play("Idle", 0.15)
	selected_start = actors[selected].position
	max_jump_height = 0.0

func _play(clip: String, blend := 0.12) -> void:
	if current_clip != clip:
		players[selected].play(clip, blend)
		current_clip = clip
		if verify:
			if not checks.has("transitions"):
				checks["transitions"] = []
			checks["transitions"].append({"character": CHARACTERS[selected], "clip": clip, "time_s": elapsed})

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode >= KEY_1 and event.keycode <= KEY_3:
			_select(event.keycode - KEY_1)
		elif event.keycode == KEY_E:
			_play("Talk")
			action_remaining = 2.0
		elif event.keycode == KEY_T:
			_toggle_toon()
		elif event.keycode == KEY_R:
			actors[selected].position = Vector3((selected - 1) * 1.6, 0, 0)
			models[selected].rotation = Vector3.ZERO
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
		yaw -= event.relative.x * 0.006
		pitch = clampf(pitch - event.relative.y * 0.004, -0.5, 0.5)
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			distance = maxf(1.5, distance - 0.3)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			distance = minf(9.0, distance + 0.3)

func _physics_process(delta: float) -> void:
	if actors.is_empty():
		return
	elapsed += delta
	if verify:
		_verification_tick()
	var body := actors[selected]
	var axis := Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
	var movement := Vector3(axis.x, 0, axis.y).rotated(Vector3.UP, yaw)
	var speed := RUN_SPEED if Input.is_action_pressed("sprint") else WALK_SPEED
	body.velocity.x = movement.x * speed
	body.velocity.z = movement.z * speed
	if not body.is_on_floor():
		body.velocity.y -= 16.0 * delta
	if Input.is_action_just_pressed("jump") and body.is_on_floor():
		body.velocity.y = 5.2
		_play("Jump", 0.08)
		action_remaining = 0.22
	if Input.is_action_just_pressed("attack") and body.is_on_floor():
		_play("Attack", 0.07)
		action_remaining = players[selected].get_animation("Attack").length
	if movement.length_squared() > 0.01:
		models[selected].rotation.y = lerp_angle(models[selected].rotation.y, atan2(movement.x, movement.z), delta*12)
	action_remaining = maxf(0.0, action_remaining-delta)
	if action_remaining == 0.0:
		if not body.is_on_floor():
			_play("Fall")
		elif movement.length_squared() > 0.01:
			_play("Run" if Input.is_action_pressed("sprint") else "Walk")
		else:
			_play("Idle")
	var was_grounded := body.is_on_floor()
	body.move_and_slide()
	if not was_grounded and body.is_on_floor() and current_clip in ["Jump", "Fall"]:
		_play("Land", 0.06)
		action_remaining = minf(0.25, players[selected].get_animation("Land").length)
	max_jump_height = maxf(max_jump_height, body.position.y)
	for index in actors.size():
		if index != selected:
			actors[index].velocity = Vector3(0, -1, 0)
			actors[index].move_and_slide()
	var focus := body.position + Vector3.UP*0.9
	camera.position = focus + Vector3(sin(yaw)*distance, 0.5+pitch*distance, cos(yaw)*distance)
	camera.look_at(focus)
	status.text = "%s · %s · %s\n模型与骨骼动作验证；美术精修持续进行" % [LABELS[selected], current_clip, "Toon" if toon_enabled else "源材质"]

func _toggle_toon() -> void:
	toon_enabled = not toon_enabled
	for model in models:
		for node in model.find_children("*", "MeshInstance3D", true, false):
			var mesh := node as MeshInstance3D
			for surface in mesh.mesh.get_surface_count():
				var key := "%s:%s" % [mesh.get_instance_id(), surface]
				if not original_materials.has(key):
					original_materials[key] = mesh.get_active_material(surface)
				var original := original_materials[key] as StandardMaterial3D
				if toon_enabled and original:
					var material := ShaderMaterial.new()
					material.shader = load("res://scenes/character_lab/character_toon.gdshader")
					material.set_shader_parameter("albedo_texture", original.albedo_texture)
					material.set_shader_parameter("albedo_color", original.albedo_color)
					mesh.set_surface_override_material(surface, material)
				else:
					mesh.set_surface_override_material(surface, original_materials[key])

func _verification_tick() -> void:
	var step := int(elapsed/0.8)
	if step == verify_step:
		return
	verify_step = step
	match step:
		1:
			_capture("white_idle")
			Input.action_press("move_backward")
		2:
			_capture("white_walk")
			checks["walk_distance"] = actors[0].position.distance_to(initial_position)
			Input.action_press("sprint")
		3:
			_capture("white_run")
			Input.action_release("move_backward")
			Input.action_release("sprint")
			Input.action_press("jump")
			_capture_after("white_jump", 0.24)
		4:
			Input.action_release("jump")
			checks["jump_height"] = max_jump_height
			Input.action_press("attack")
			_capture_after("white_attack", 0.30)
		5:
			Input.action_release("attack")
			_select(1)
		6:
			_capture("orange_idle")
			Input.action_press("move_backward")
			Input.action_press("sprint")
		7:
			_capture("orange_run")
			checks["orange_run_distance"] = actors[1].position.distance_to(selected_start)
			Input.action_release("move_backward")
			Input.action_release("sprint")
			Input.action_press("jump")
			_capture_after("orange_jump", 0.24)
		8:
			Input.action_release("jump")
			checks["orange_jump_height"] = max_jump_height
			Input.action_press("attack")
			_capture_after("orange_attack", 0.30)
		9:
			Input.action_release("attack")
			_select(2)
		10:
			_capture("purple_idle")
			Input.action_press("move_backward")
			Input.action_press("sprint")
		11:
			_capture("purple_run")
			checks["purple_run_distance"] = actors[2].position.distance_to(selected_start)
			Input.action_release("move_backward")
			Input.action_release("sprint")
			Input.action_press("jump")
			_capture_after("purple_jump", 0.24)
		12:
			Input.action_release("jump")
			checks["purple_jump_height"] = max_jump_height
			Input.action_press("attack")
			_capture_after("purple_attack", 0.30)
		13:
			Input.action_release("attack")
		14:
			_toggle_toon()
		15:
			_capture("purple_toon")
		16:
			for index in actors.size():
				actors[index].position = Vector3((index-1)*1.6, 0, 0)
				models[index].rotation = Vector3.ZERO
				players[index].play("Idle", 0.15)
			if toon_enabled:
				_toggle_toon()
			_select(1)
		17:
			_capture("three_characters")
			checks["renderer"] = RenderingServer.get_current_rendering_method()
			checks["engine"] = Engine.get_version_info().string
			checks["movement_ok"] = checks.get("walk_distance", 0.0) > 0.5 and checks.get("orange_run_distance", 0.0) > 1.0 and checks.get("purple_run_distance", 0.0) > 1.0
			checks["jump_ok"] = checks.get("jump_height", 0.0) > 0.3 and checks.get("orange_jump_height", 0.0) > 0.3 and checks.get("purple_jump_height", 0.0) > 0.3
			checks["skeletons_ok"] = true
			for character in checks["characters"]:
				checks["skeletons_ok"] = checks["skeletons_ok"] and character.bones >= 26 and character.missing_clips.is_empty()
			var file := FileAccess.open(evidence_path.path_join("godot_report.json"), FileAccess.WRITE)
			file.store_string(JSON.stringify(checks, "\t"))
			print("CHARACTER_VERIFICATION ", JSON.stringify(checks))
			get_tree().quit(0 if checks["movement_ok"] and checks["jump_ok"] and checks["skeletons_ok"] else 1)

func _capture(label: String) -> void:
	# Read the completed frame before this physics tick changes input/state.
	# Waiting here would capture the NEXT clip under the previous clip's name.
	var image := get_viewport().get_texture().get_image()
	image.save_png(evidence_path.path_join(label+".png"))
	if not checks.has("captures"):
		checks["captures"] = []
	checks["captures"].append({"file": label+".png", "character": CHARACTERS[selected], "clip": current_clip, "animation_time": players[selected].current_animation_position, "position": [actors[selected].position.x, actors[selected].position.y, actors[selected].position.z]})

func _capture_after(label: String, delay: float) -> void:
	await get_tree().create_timer(delay).timeout
	_capture(label)
