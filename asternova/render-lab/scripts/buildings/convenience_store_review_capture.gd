extends Node
## Convenience store x Aster 2K review capture (two shots, one camera).
## Shot A (frame 90):  front-glass see-through composition — Aster at the
##                     open entrance, warm interior visible through the glass.
## Shot B (frame 180): interior walkthrough proof — Aster inside the hollow
##                     shell at the counter aisle, no air-wall ejection.
const OUT_A := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/environment/convenience_store_front_glass_review.png"
const OUT_B := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/environment/convenience_store_interior_walkthrough.png"

var frame: int = 0


func _ready() -> void:
	var win := get_window()
	win.size = Vector2i(2048, 1152)
	var screen := DisplayServer.screen_get_size(win.current_screen)
	win.position = DisplayServer.screen_get_position(win.current_screen) \
			+ (screen - win.size) / 2
	var sun: DirectionalLight3D = get_tree().current_scene.get_node("SunLight")
	# 下午 14:30 晴空：暖阳 + 冷天光对冲，阴影朝向画面深处
	sun.look_at_from_position(Vector3(-6.0, 9.0, -5.0), Vector3(0, 0, 0))
	print("[cs_review] scene ready, window=", win.size)


func _process(_delta: float) -> void:
	frame += 1
	var cam: Camera3D = get_tree().current_scene.get_node("ReviewCamera")
	if frame == 30:
		cam.look_at_from_position(Vector3(0.3, 1.5, -12.6), Vector3(1.9, 1.35, -4.0))
		cam.fov = 45.0
		cam.current = true
	elif frame == 90:
		_capture(OUT_A)
	elif frame == 120:
		cam.look_at_from_position(Vector3(-2.4, 1.6, 2.6), Vector3(2.0, 1.15, -2.2))
		cam.fov = 50.0
	elif frame == 180:
		_capture(OUT_B)
	elif frame > 185:
		get_tree().quit(0)


func _capture(path: String) -> void:
	var img: Image = get_viewport().get_texture().get_image()
	DirAccess.make_dir_absolute(path.get_base_dir())
	var err: Error = img.save_png(path)
	if err == OK:
		print("[cs_review] saved: ", path, " size=", img.get_size())
	else:
		push_error("[cs_review] save failed err=%d" % err)
		get_tree().quit(1)
