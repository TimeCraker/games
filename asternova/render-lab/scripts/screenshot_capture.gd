extends Node

var frame_count: int = 0
var stage: Node3D
var quality_mgr: CanvasLayer
var orbit_cam: Node3D

func _ready() -> void:
	stage = get_tree().current_scene
	quality_mgr = stage.get_node("QualityManager")
	orbit_cam = stage.get_node("OrbitCameraPivot")
	print("ScreenshotCapture helper ready")

func _process(_delta: float) -> void:
	frame_count += 1
	
	# 等待 45 帧让樱花粒子充分发射、光影与后处理完全就绪
	if frame_count == 40:
		quality_mgr.set_quality_tier(quality_mgr.QualityTier.HIGH)
	elif frame_count == 55:
		_capture("screenshot_high.png")
	elif frame_count == 60:
		quality_mgr.set_quality_tier(quality_mgr.QualityTier.MEDIUM)
	elif frame_count == 75:
		_capture("screenshot_medium.png")
	elif frame_count == 80:
		quality_mgr.set_quality_tier(quality_mgr.QualityTier.LOW)
	elif frame_count == 95:
		_capture("screenshot_low.png")
	elif frame_count == 100:
		# 切回高画质并拉近相机特写 Aster 头部与半身：清冷眼神、细致腮红与珍珠银白发丝
		quality_mgr.set_quality_tier(quality_mgr.QualityTier.HIGH)
		if orbit_cam:
			orbit_cam._current_distance = 1.18
			orbit_cam.target_offset = Vector3(0, 1.26, 0)
			orbit_cam._pitch = 0.02
			orbit_cam._yaw = 0.08
			orbit_cam._update_camera_transform()
	elif frame_count == 115:
		_capture("screenshot_aster_closeup.png")
	elif frame_count == 120:
		# 拉大广角查看整条黄昏樱花商店街全景与深远纵深透视
		if orbit_cam:
			orbit_cam._current_distance = 4.5
			orbit_cam.target_offset = Vector3(0, 1.10, 0)
			orbit_cam._pitch = -0.12
			orbit_cam._yaw = -0.55
			orbit_cam._update_camera_transform()
	elif frame_count == 135:
		_capture("screenshot_street_wide.png")
		print("All screenshots captured successfully!")
		get_tree().quit(0)

func _capture(filename: String) -> void:
	var img: Image = get_viewport().get_texture().get_image()
	var out_dir: String = "c:/Users/TimeCraker/Desktop/my-workspace/games/asternova/art/render_previews"
	DirAccess.make_dir_absolute(out_dir)
	var full_path: String = out_dir + "/" + filename
	var err: Error = img.save_png(full_path)
	if err == OK:
		print("Saved screenshot: ", full_path, " size: ", img.get_size())
	else:
		print("Failed to save screenshot: ", full_path, " err: ", err)
