extends Node

var frame: int = 0
var stage: Node3D
var cam_front: Camera3D
var cam_back: Camera3D
var cam_side: Camera3D
var cam_closeup: Camera3D

func _ready() -> void:
	stage = get_tree().current_scene
	cam_front = stage.get_node("CamFront")
	cam_back = stage.get_node("CamBack")
	cam_side = stage.get_node("CamSide")
	cam_closeup = stage.get_node("CamCloseup")
	print("TurnaroundCapture ready. Cameras:", cam_front, cam_back, cam_side, cam_closeup)
	_activate_camera(cam_front)

func _activate_camera(cam: Camera3D) -> void:
	for c in [cam_front, cam_back, cam_side, cam_closeup]:
		if c:
			c.current = (c == cam)
	_align_lighting_with_camera(cam)

func _align_lighting_with_camera(cam: Camera3D) -> void:
	if not cam or not stage:
		return
	var key_light: DirectionalLight3D = stage.get_node_or_null("KeyLight")
	var fill_light: DirectionalLight3D = stage.get_node_or_null("FillLight")
	
	var cam_pos: Vector3 = cam.global_position
	var target: Vector3 = Vector3(0, 0.95, 0)
	if cam == cam_closeup:
		target = Vector3(0, 1.54, 0)
	
	var forward: Vector3 = (target - cam_pos).normalized()
	var right: Vector3 = forward.cross(Vector3.UP).normalized()
	var up: Vector3 = right.cross(forward).normalized()
	
	if key_light:
		var key_pos: Vector3 = cam_pos + right * 0.35 + up * 0.30
		key_light.global_position = key_pos
		key_light.look_at(target, Vector3.UP)
		key_light.light_energy = 0.32
		
	if fill_light:
		var fill_pos: Vector3 = cam_pos - right * 0.30 + up * 0.20
		fill_light.global_position = fill_pos
		fill_light.look_at(target, Vector3.UP)
		fill_light.light_energy = 0.15

func _process(_delta: float) -> void:
	frame += 1
	
	if frame == 15:
		_activate_camera(cam_front)
	elif frame == 25:
		_save_shot("aster_front.png")
		_activate_camera(cam_back)
	elif frame == 35:
		_save_shot("aster_back.png")
		_activate_camera(cam_side)
	elif frame == 45:
		_save_shot("aster_side.png")
		_activate_camera(cam_closeup)
	elif frame == 55:
		_save_shot("aster_closeup.png")
		print("All turnaround shots captured!")
		get_tree().quit(0)

func _save_shot(filename: String) -> void:
	var img: Image = get_viewport().get_texture().get_image()
	var out_dir: String = "c:/Users/TimeCraker/Desktop/my-workspace/games/asternova/art/render_previews"
	DirAccess.make_dir_absolute(out_dir)
	var full_path: String = out_dir + "/" + filename
	var err: Error = img.save_png(full_path)
	if err == OK:
		print("Saved turnaround screenshot: ", full_path, " size: ", img.get_size())
	else:
		print("Error saving: ", err)
