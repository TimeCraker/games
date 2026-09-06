extends Node
## Convenience store x Aster 2K review capture (two shots, one camera).
## Time-driven state machine — frame-count scheduling skips on load hitches.
## Shot A: front-glass see-through composition (Aster at the open entrance).
## Shot B: interior walkthrough proof (Aster in the aisle by the shelves).

const OUT_A := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/environment/convenience_store_front_glass_review.png"
const OUT_B := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/environment/convenience_store_interior_walkthrough.png"

var t := 0.0
var step := 0


func _ready() -> void:
	var win := get_window()
	win.size = Vector2i(2048, 1152)
	var screen := DisplayServer.screen_get_size(win.current_screen)
	win.position = DisplayServer.screen_get_position(win.current_screen) \
			+ (screen - win.size) / 2
	_set_cam(Vector3(0.6, 1.7, -15.5), Vector3(0.3, 1.75, -4.5), 48.0)
	print("[cs_review] scene ready, window=", win.size)


func _set_cam(pos: Vector3, target: Vector3, fov: float) -> void:
	var cam: Camera3D = get_tree().current_scene.get_node("ReviewCamera")
	cam.global_transform = Transform3D(Basis.looking_at(target - pos, Vector3.UP), pos)
	cam.fov = fov
	cam.current = true


func _process(delta: float) -> void:
	t += delta
	if step == 0 and t >= 1.5:
		_capture(OUT_A)
		_set_cam(Vector3(1.9, 1.62, -3.6), Vector3(0.6, 1.05, 1.2), 48.0)
		step = 1
	elif step == 1 and t >= 3.0:
		_capture(OUT_B)
		print("[cs_review] cam B at ", get_tree().current_scene.get_node(
				"ReviewCamera").global_position)
		step = 2
	elif step == 2 and t >= 3.3:
		get_tree().quit(0)


func _capture(path: String) -> void:
	var cam: Camera3D = get_tree().current_scene.get_node("ReviewCamera")
	print("[cs_review] capture ", path.get_file(), " cam=", cam.global_position,
			" fov=", cam.fov)
	var img: Image = get_viewport().get_texture().get_image()
	DirAccess.make_dir_absolute(path.get_base_dir())
	var err: Error = img.save_png(path)
	if err == OK:
		print("[cs_review] saved: ", path, " size=", img.get_size())
	else:
		push_error("[cs_review] save failed err=%d" % err)
		get_tree().quit(1)
