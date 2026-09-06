extends Node
## Ground pavement review capture (第四执行组).
## Frames the Aster heroine standing on the reworked south plaza (ivory tiles +
## tactile paving) where it meets the asphalt central slope ramp, then saves one
## true-engine 2K (2048x1152) screenshot.

const OUT_PATH := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/environment/ground_pavement_review.png"

var frame: int = 0


func _ready() -> void:
	var win := get_window()
	win.size = Vector2i(2048, 1152)
	var screen := DisplayServer.screen_get_size(win.current_screen)
	win.position = DisplayServer.screen_get_position(win.current_screen) \
			+ (screen - win.size) / 2

	var stage := get_tree().current_scene
	var cam: Camera3D = stage.get_node("ReviewCamera")
	# 透视俯角 35°（atan(6.72/9.60)=35.0°）：西南角东北望 —— 左下米白方砖人行道+黄色盲道带、
	# 中央坡道交界与东缘白实线透视线、右侧 Aster 站立点；路东紫灰地块只留远角
	cam.look_at_from_position(Vector3(-6.0, 7.22, 23.0), Vector3(0.0, 0.5, 15.5))
	cam.fov = 40.0
	cam.current = true

	var sun: DirectionalLight3D = stage.get_node("SunLight")
	sun.look_at_from_position(Vector3(-6.0, 16.0, 26.0), Vector3(0.0, 0.0, 10.0))

	print("[ground_review] scene ready, window=", win.size)


func _process(_delta: float) -> void:
	frame += 1
	# 等待 45 帧：材质导入、阴影与 SSAO 完全收敛后再出图
	if frame == 45:
		_capture()
	elif frame >= 300:
		push_error("[ground_review] capture timed out")
		get_tree().quit(1)


func _capture() -> void:
	var img: Image = get_viewport().get_texture().get_image()
	DirAccess.make_dir_absolute(OUT_PATH.get_base_dir())
	var err: Error = img.save_png(OUT_PATH)
	if err == OK:
		print("[ground_review] saved: ", OUT_PATH, " size=", img.get_size())
	else:
		push_error("[ground_review] save failed err=%d" % err)
	get_tree().quit(0 if err == OK else 1)
