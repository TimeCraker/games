extends "res://scenes/character_lab/character_lab.gd"
## Purple-only replacement in an independent copy of the existing lab.

const REWORK = preload("res://models/characters/rework/purple_repaired.glb")
const REVIEW_CLIPS = ["Idle", "Walk", "Run", "Sprint", "Jump", "Fall", "Land", "Attack", "Talk"]
var inspect_mode := false
var review_paused := false
var frame_times: Array[float] = []

func _process(delta: float) -> void:
	frame_times.append(delta * 1000.0)

func _ready() -> void:
	super._ready()
	_select(2)
	if "--verify-purple-rework" in OS.get_cmdline_user_args():
		_verify_rework()
	elif "--record-purple-rework" in OS.get_cmdline_user_args():
		_record_rework()

func _add_actor(index: int) -> void:
	if index != 2:
		super._add_actor(index)
		return
	var body := CharacterBody3D.new()
	body.position = Vector3(1.6, 0, 0)
	var collider := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.height = 1.65
	capsule.radius = 0.23
	collider.shape = capsule
	collider.position.y = 0.825
	body.add_child(collider)
	var model := REWORK.instantiate() as Node3D
	body.add_child(model)
	add_child(body)
	var player := model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	assert(player != null, "Purple AnimationPlayer missing")
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
	var label := Label.new()
	label.position = Vector2(24, 24)
	label.text = "紫色返工 · 静态/变形待美术验收\nWASD 移动 · Shift 跑步 · 空格 跳跃 · 左键 攻击 · E 交谈\nF1–F9 查看九段动作 · L 休止 · P 暂停 · O 慢放 · G 恢复移动\n右键 环绕 · 滚轮 缩放 · T 材质对比 · 1/2 旧原型 · 3 紫色返工"
	label.add_theme_font_size_override("font_size", 20)
	canvas.add_child(label)
	status = Label.new()
	status.position = Vector2(24, 154)
	canvas.add_child(status)

func _review_camera() -> void:
	var target := actors[selected].position + Vector3(0, 0.95, 0)
	camera.position = target + Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch)) * distance
	camera.look_at(target)
	status.text = "休止姿态" if current_clip == "Rest" else current_clip
	if review_paused:
		status.text += " · 已暂停"
	status.text += " · %.2fx" % players[selected].speed_scale

func _physics_process(delta: float) -> void:
	if inspect_mode or review_paused:
		_review_camera()
		return
	super._physics_process(delta)

func _unhandled_input(event: InputEvent) -> void:
	super._unhandled_input(event)
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode >= KEY_F1 and event.keycode <= KEY_F9:
			inspect_mode = true
			review_paused = false
			current_clip = REVIEW_CLIPS[event.keycode - KEY_F1]
			players[selected].play(current_clip)
		elif event.keycode == KEY_L:
			inspect_mode = true
			review_paused = false
			current_clip = "Rest"
			players[selected].stop()
			(models[selected].find_child("Skeleton3D", true, false) as Skeleton3D).reset_bone_poses()
		elif event.keycode == KEY_P:
			review_paused = not review_paused
			if review_paused:
				players[selected].pause()
			else:
				players[selected].play()
		elif event.keycode == KEY_O:
			players[selected].speed_scale = 0.25 if players[selected].speed_scale == 1.0 else 1.0
		elif event.keycode == KEY_G:
			inspect_mode = false
			review_paused = false
			action_remaining = 0
			current_clip = ""
			players[selected].speed_scale = 1

func _save_rework_frame(directory: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	var error := get_viewport().get_texture().get_image().save_png(directory.path_join(name + ".png"))
	assert(error == OK, "Screenshot failed: " + name)

func _verify_rework() -> void:
	var directory := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--evidence="):
			directory = argument.trim_prefix("--evidence=")
	assert(not directory.is_empty(), "Missing evidence directory")
	DirAccess.make_dir_recursive_absolute(directory)
	inspect_mode = true
	var skeleton := models[2].find_child("Skeleton3D", true, false) as Skeleton3D
	players[2].stop()
	skeleton.reset_bone_poses()
	current_clip = "Rest"
	await get_tree().create_timer(0.5).timeout
	await _save_rework_frame(directory, "rest")
	var clips: Array[Dictionary] = []
	for clip in REVIEW_CLIPS:
		assert(players[2].has_animation(clip), "Missing clip: " + clip)
		var animation := players[2].get_animation(clip)
		current_clip = clip
		players[2].play(clip)
		players[2].seek(minf(0.24, animation.length * 0.4), true)
		players[2].pause()
		await get_tree().create_timer(0.15).timeout
		await _save_rework_frame(directory, clip.to_lower())
		clips.append({"name": clip, "duration_s": animation.length})
	inspect_mode = false
	players[2].play("Idle")
	current_clip = "Idle"
	action_remaining = 0
	await get_tree().create_timer(0.3).timeout
	var start := actors[2].position
	Input.action_press("move_forward")
	await get_tree().create_timer(0.8).timeout
	await _save_rework_frame(directory, "moving_walk")
	var walk_distance := actors[2].position.distance_to(start)
	Input.action_press("sprint")
	start = actors[2].position
	await get_tree().create_timer(0.8).timeout
	await _save_rework_frame(directory, "moving_run")
	var run_distance := actors[2].position.distance_to(start)
	Input.action_release("move_forward")
	Input.action_release("sprint")
	Input.action_press("jump")
	await get_tree().physics_frame
	Input.action_release("jump")
	await get_tree().create_timer(0.2).timeout
	await _save_rework_frame(directory, "moving_jump")
	var jump_height := actors[2].position.y
	await get_tree().create_timer(1.0).timeout
	await _save_rework_frame(directory, "landed")
	var landed := actors[2].is_on_floor()
	Input.action_press("attack")
	await get_tree().physics_frame
	Input.action_release("attack")
	await get_tree().create_timer(0.2).timeout
	await _save_rework_frame(directory, "game_attack")
	assert(walk_distance > 0.3 and run_distance > walk_distance and jump_height > 0.3 and landed)
	frame_times.sort()
	var report := {"engine": Engine.get_version_info().string,
		"renderer": RenderingServer.get_current_rendering_method(),
		"resolution": get_viewport().get_visible_rect().size,
		"bones": skeleton.get_bone_count(), "clips": clips,
		"walk_distance_m": walk_distance, "run_distance_m": run_distance,
		"jump_height_m": jump_height, "landed": landed,
		"frame_ms_median": frame_times[int(frame_times.size() / 2)],
		"frame_ms_p95": frame_times[int(frame_times.size() * 0.95)],
		"art_approved": false, "deformation_approved": false}
	var file := FileAccess.open(directory.path_join("runtime_report.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	get_tree().quit()

func _record_rework() -> void:
	var directory := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--evidence="):
			directory = argument.trim_prefix("--evidence=")
	assert(not directory.is_empty(), "Missing evidence directory")
	DirAccess.make_dir_recursive_absolute(directory)
	inspect_mode = true
	for index in [0, 1]:
		actors[index].hide()
	yaw = 0.22
	pitch = 0.03
	distance = 3.5
	var captured := 0
	# Consecutive 30 fps samples of the real imported AnimationPlayer.
	# Playback time is deterministic; the output is an animation review video.
	for clip in ["Idle", "Walk", "Run", "Jump", "Attack", "Talk"]:
		current_clip = clip
		var animation := players[2].get_animation(clip)
		players[2].play(clip)
		players[2].pause()
		for index in range(60):
			players[2].seek(fmod(index / 30.0, animation.length), true)
			_review_camera()
			await RenderingServer.frame_post_draw
			var image := get_viewport().get_texture().get_image()
			image.resize(960, 540, Image.INTERPOLATE_LANCZOS)
			var error := image.save_png(directory.path_join("frame_%04d.png" % captured))
			assert(error == OK, "Video frame capture failed")
			captured += 1
			await get_tree().process_frame
	var file := FileAccess.open(directory.path_join("capture_report.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"fps": 30, "frames": captured,
		"source": "purple_repaired.glb", "sampling": "consecutive AnimationPlayer seeks",
		"art_approved": false, "deformation_approved": false}, "\t"))
	get_tree().quit()
