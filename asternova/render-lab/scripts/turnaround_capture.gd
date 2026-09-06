extends Node
## Turnaround stage capture: frames the assembled Aster prefab on the front camera
## and saves one true-engine 2K screenshot for the NPR review board.

const OUT_PATH := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/characters/aster/01_godot_npr_review.png"

var frame: int = 0
var stage: Node3D
var cam_front: Camera3D


func _ready() -> void:
	stage = get_tree().current_scene
	cam_front = stage.get_node("CamFront")
	print("TurnaroundCapture ready. cam_front=", cam_front)
	_window_2k()
	_activate_camera(cam_front)


func _window_2k() -> void:
	var win := get_window()
	win.size = Vector2i(2048, 2048)
	var screen := DisplayServer.screen_get_size(win.current_screen)
	win.position = DisplayServer.screen_get_position(win.current_screen) \
			+ (screen - win.size) / 2


func _activate_camera(cam: Camera3D) -> void:
	for c in stage.get_children():
		if c is Camera3D:
			c.current = (c == cam)
	_align_lighting_with_camera(cam)


func _align_lighting_with_camera(cam: Camera3D) -> void:
	if not cam or not stage:
		return
	var key_light: DirectionalLight3D = stage.get_node_or_null("KeyLight")
	var fill_light: DirectionalLight3D = stage.get_node_or_null("FillLight")

	var cam_pos: Vector3 = cam.global_position
	var target: Vector3 = Vector3(0, 0.86, 0)
	var forward: Vector3 = (target - cam_pos).normalized()
	var right: Vector3 = forward.cross(Vector3.UP).normalized()
	var up: Vector3 = right.cross(forward).normalized()

	if key_light:
		key_light.global_position = cam_pos + right * 2.6 + up * 0.5
		key_light.look_at(target, Vector3.UP)
		key_light.light_energy = 0.75
	if fill_light:
		fill_light.global_position = cam_pos - right * 1.4 + up * 0.5
		fill_light.look_at(target, Vector3.UP)
		fill_light.light_energy = 0.25


func _process(_delta: float) -> void:
	frame += 1
	if frame == 30:
		_capture()
		frame = 31


func _capture() -> void:
	await RenderingServer.frame_post_draw
	var img: Image = get_viewport().get_texture().get_image()
	DirAccess.make_dir_recursive_absolute(OUT_PATH.get_base_dir())
	var err: Error = img.save_png(OUT_PATH)
	if err == OK:
		print("Saved NPR review screenshot: ", OUT_PATH, " size: ", img.get_size())
	else:
		print("Error saving: ", err)
	get_tree().quit(0)
