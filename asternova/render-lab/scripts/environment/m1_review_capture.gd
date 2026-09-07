extends Node
## M1 Endfield street sandbox 2K review capture (M1 终极街区沙盒总装配).
## M1_SHOT=street (默认) 主机位全景: 南广场路面向北微仰视坡道+便利店,
##   前景斑马线/井盖, Aster 黄金分割受光位, 远景鸟居与清冷晴空 -> m1_endfield_street_high_2k.png
## M1_SHOT=store 便利店冷暖特写: 店门暖光溢出+冰蓝贩卖机+Aster 侧面 -> m1_convenience_store_warmth_closeup_2k.png
## M1_SHOT=tiers 低/中/高三档同机位对比帧 (qa 中间产物, 由 compose 脚本合成看板)

const OUT_DIR := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/scenes"
const QA_DIR := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/scenes/qa"

var frame: int = 0
var shot: String = "street"


func _ready() -> void:
	shot = OS.get_environment("M1_SHOT")
	if shot == "":
		shot = "street"
	var win := get_window()
	win.size = Vector2i(2048, 1152)
	var screen := DisplayServer.screen_get_size(win.current_screen)
	win.position = DisplayServer.screen_get_position(win.current_screen) \
			+ (screen - win.size) / 2

	var stage := get_tree().current_scene
	var cam: Camera3D = stage.get_node("ReviewCamera")
	match shot:
		"store":
			# 便利店冷暖特写: 精确换算 434f061 过审 Shot B 机位 (店内右前角斜视过道,
			# 暖光货架+彩色商品为主体), Aster 立于过道面向西货架
			cam.look_at_from_position(Vector3(-12.45, 1.62, 21.9), Vector3(-17.25, 1.05, 20.6))
			cam.fov = 48.0
			var aster := stage.get_node_or_null("CharacterAster")
			if aster is Node3D:
				aster.position = Vector3(-15.45, 0.2, 20.35)
				aster.rotation.y = deg_to_rad(30.0)   # 面向西货架: 暖 LED 打亮右侧脸
		"corner":
			# 街角生活道具特写: 东南上空望西北, HouseA/B 檐下空调外机群 +
			# 东西挡墙贴花 + 电线杆与跨街电缆一并入画
			cam.look_at_from_position(Vector3(7.5, 3.2, 21.0), Vector3(-7.5, 5.2, -2.0))
			cam.fov = 50.0
		"overview":
			# 标定俯瞰: 东北空地上空 34m, 看全街区装配落位与残伪影排查
			cam.look_at_from_position(Vector3(10.0, 34.0, 14.0), Vector3(-3.0, 0.0, -20.0))
			cam.fov = 50.0
		"topdown":
			# 垂直俯拍广场: 材质落位/井盖/树位/阴影方向排查
			cam.look_at_from_position(Vector3(0.0, 26.0, 30.0), Vector3(-1.0, 0.0, 18.0))
			cam.fov = 55.0
		_:
			# 主机位: 立于南广场路面向北微仰视, 白实线/斑马线横贯前景,
			# 井盖中景, Aster 黄金分割, 坡道顶鸟居收边, 清冷晴空
			cam.look_at_from_position(Vector3(1.2, 1.7, 28.2), Vector3(-2.6, 1.1, 14.5))
			cam.fov = 44.0
	cam.current = true

	# 诊断开关 (仅评审迭代用, 不改变母版默认状态)
	var lighting := stage.get_node("EndfieldLighting")
	var sun: DirectionalLight3D = lighting.get_node("SunLight")
	var env_res: Environment = lighting.get_node("WorldEnvironment").environment
	if OS.get_environment("M1_FOG") == "0":
		env_res.volumetric_fog_enabled = false
	var sun_v := OS.get_environment("M1_SUN")
	if sun_v != "":
		sun.light_energy = float(sun_v)
	var expo_v := OS.get_environment("M1_EXPOSURE")
	if expo_v != "":
		env_res.tonemap_exposure = float(expo_v)
	var amb_v := OS.get_environment("M1_AMBIENT")
	if amb_v != "":
		env_res.ambient_light_energy = float(amb_v)
	if OS.get_environment("M1_SSR") == "0":
		env_res.ssr_enabled = false
	if OS.get_environment("M1_PROBE") == "0":
		var probe: ReflectionProbe = lighting.get_node_or_null("StreetReflectionProbe")
		if probe:
			probe.visible = false
	print("[m1_capture] sun.energy=", sun.light_energy, " fog=", env_res.volumetric_fog_enabled,
			" exposure=", env_res.tonemap_exposure,
			" ambient=", env_res.ambient_light_energy,
			" sun_basis_z=", sun.global_transform.basis.z)

	# 评审出图不带 HUD; 三档切换仍由 QualityManager 驱动
	var quality: CanvasLayer = stage.get_node("QualityManager")
	quality.visible = false

	# A-pose 残留修正: 上臂沿骨骼本地 Z 轴补转至自然垂臂 (L 负 R 正镜像), 前臂微弯
	var aster_node := stage.get_node_or_null("CharacterAster")
	if aster_node is Node3D:
		var skeletons := aster_node.find_children("*", "Skeleton3D", true, false)
		if not skeletons.is_empty():
			var skel: Skeleton3D = skeletons[0]
			for entry: Array in [["L_Upperarm", -0.85], ["R_Upperarm", 0.85],
					["L_Forearm", -0.25], ["R_Forearm", 0.25]]:
				var bone_idx := skel.find_bone(entry[0])
				if bone_idx >= 0:
					var rest: Quaternion = skel.get_bone_rest(bone_idx).basis.get_rotation_quaternion()
					skel.set_bone_pose_rotation(bone_idx,
							rest * Quaternion(Vector3(0, 0, 1), entry[1]))
			print("[m1_capture] aster natural pose applied")

	print("[m1_capture] scene ready, shot=", shot, " window=", win.size)


func _process(_delta: float) -> void:
	frame += 1
	match shot:
		"tiers":
			match frame:
				10:
					_set_tier(0)          # LOW: 关泛光/SSAO/SSR, 40 花瓣
				50:
					_capture("m1_qa_tier_low.png", QA_DIR)
				55:
					_set_tier(1)          # MEDIUM: 120fps/2x MSAA/标准泛光
				95:
					_capture("m1_qa_tier_medium.png", QA_DIR)
				100:
					_set_tier(2)          # HIGH: 4x MSAA/全特效/200 花瓣
				150:
					_capture("m1_qa_tier_high.png", QA_DIR)
			if frame >= 400:
				push_error("[m1_capture] tiers capture timed out")
				get_tree().quit(1)
		_:
			# 等待 60 帧: 反射探针烘焙/体积雾重投影/花瓣 preprocess 完全收敛
			if frame == 60:
				var out_name := ""
				match shot:
					"street":
						out_name = "m1_endfield_street_high_2k.png"
					"store":
						out_name = "m1_convenience_store_warmth_closeup_2k.png"
					"corner":
						out_name = "m1_street_corner_props_2k.png"
					_:
						out_name = "m1_qa_%s.png" % shot
				_capture(out_name, QA_DIR if out_name.begins_with("m1_qa_") else OUT_DIR)
			elif frame >= 300:
				push_error("[m1_capture] capture timed out")
				get_tree().quit(1)


func _set_tier(tier: int) -> void:
	var stage := get_tree().current_scene
	var quality: CanvasLayer = stage.get_node("QualityManager")
	quality.call("set_quality_tier", tier)
	print("[m1_capture] tier -> ", tier)


func _capture(file_name: String, dir: String) -> void:
	var img: Image = get_viewport().get_texture().get_image()
	var path := dir + "/" + file_name
	DirAccess.make_dir_absolute(dir)
	var err: Error = img.save_png(path)
	if err == OK:
		print("[m1_capture] saved: ", path, " size=", img.get_size())
	else:
		push_error("[m1_capture] save failed err=%d path=%s" % [err, path])
	# tiers 模式连续出三帧后由最后一帧退出; 单图模式立即退出
	if shot != "tiers":
		get_tree().quit(0 if err == OK else 1)
	elif file_name.contains("high"):
		get_tree().quit(0 if err == OK else 1)
