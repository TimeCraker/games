extends Node
## Vending machine x Aster scale review capture.
## Frames the 1.830m dual vending machine next to the 1.650m Aster heroine on
## the sidewalk, then saves one true-engine 2K (2048x1152) screenshot.

const OUT_PATH := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/environment/vending_machine_aster_review.png"

var frame: int = 0


func _ready() -> void:
	var win := get_window()
	win.size = Vector2i(2048, 1152)
	var screen := DisplayServer.screen_get_size(win.current_screen)
	win.position = DisplayServer.screen_get_position(win.current_screen) \
			+ (screen - win.size) / 2

	var stage := get_tree().current_scene
	var cam: Camera3D = stage.get_node("ReviewCamera")
	# 资产正面约定为 Godot -Z，因此评审相机放在 -Z 侧看向原点
	cam.look_at_from_position(Vector3(0.55, 1.42, -4.7), Vector3(0.0, 0.93, 0.0))
	cam.fov = 34.0
	cam.current = true

	var sun: DirectionalLight3D = stage.get_node("SunLight")
	sun.look_at_from_position(Vector3(-3.2, 5.6, -3.8), Vector3(0, 0.6, 0))

	print("[review] scene ready, window=", win.size)


func _process(_delta: float) -> void:
	frame += 1
	# 等待 45 帧：NPR 材质、阴影与自发光完全收敛后再出图
	if frame == 45:
		_capture()
	elif frame >= 300:
		push_error("[review] capture timed out")
		get_tree().quit(1)


func _capture() -> void:
	var img: Image = get_viewport().get_texture().get_image()
	DirAccess.make_dir_absolute(OUT_PATH.get_base_dir())
	var err: Error = img.save_png(OUT_PATH)
	if err == OK:
		print("[review] saved: ", OUT_PATH, " size=", img.get_size())
	else:
		push_error("[review] save failed err=%d" % err)
	get_tree().quit(0 if err == OK else 1)
