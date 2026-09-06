extends Node
## Ground pavement review capture (第四执行组).
## Frames the Aster heroine standing beside the sealed manhole on the south plaza
## (warm-gray tiles + tactile paving) with the asphalt ramp and its continuous
## white edge lines, then saves one true-engine 2K (2048x1152) screenshot.
## Set env GROUND_VIEW=overview for a high calibration shot of the whole block.

const OUT_PATH := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/environment/ground_pavement_review.png"
const OUT_OVERVIEW_PATH := "C:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/render_previews/environment/ground_qa/qa_scene_overview.png"

var frame: int = 0
var overview := false


func _ready() -> void:
	var mode := OS.get_environment("GROUND_VIEW")
	overview = mode == "overview" or mode == "plaza" or mode == "topdown"
	var win := get_window()
	win.size = Vector2i(2048, 1152)
	var screen := DisplayServer.screen_get_size(win.current_screen)
	win.position = DisplayServer.screen_get_position(win.current_screen) \
			+ (screen - win.size) / 2

	var stage := get_tree().current_scene
	var cam: Camera3D = stage.get_node("ReviewCamera")
	if mode == "topdown":
		# 垂直俯拍广场 (Godot z=+15..+30): 精确映射阴影边界与材质落位
		cam.look_at_from_position(Vector3(0.0, 26.0, 30.0), Vector3(-1.0, 0.0, 18.0))
		cam.fov = 55.0
	elif mode == "plaza":
		# 广场正上空俯拍: 检查顶棚/材质/井盖/阴影落位
		cam.look_at_from_position(Vector3(-3.0, 12.0, -24.0), Vector3(-4.0, 0.0, -14.0))
		cam.fov = 55.0
	elif overview:
		# 标定俯瞰: 东北空地上空 34m (避开 x>=14 的东塔楼), 看全街区 (广场+坡道+两侧建筑)
		cam.look_at_from_position(Vector3(10.0, 34.0, 14.0), Vector3(-3.0, 0.0, -20.0))
		cam.fov = 50.0
	else:
		# 商业街透视 (对标 zzz_01): 立于南广场路面向北仰视坡道, 白实线双侧汇聚,
		# 右手黄色盲道带引导线, 井盖 + Aster 前景, 坡道顶鸟居为灭点收边
		cam.look_at_from_position(Vector3(1.2, 1.7, 28.2), Vector3(-2.6, 1.1, 14.5))
		cam.fov = 44.0
	cam.current = true

	var sun: DirectionalLight3D = stage.get_node("SunLight")
	# 东东北 65° 高阳 (Godot 坐标): 地面耦合 0.885, 前景广场脱离东塔影 (影 x>=1.6);
	# 便利店前脸 0.46 受光 + ambient 填充; 井盖/盲道/白线全程受光, 拉长影可读
	sun.look_at_from_position(Vector3(28.0, 58.0, 14.0), Vector3(-2.0, 0.0, 18.0))

	var sun_node: DirectionalLight3D = stage.get_node("SunLight")
	var sun_v := OS.get_environment("GROUND_SUN")
	if sun_v != "":
		sun_node.light_energy = float(sun_v)
	if OS.get_environment("GROUND_NOSHADOW") == "1":
		sun_node.shadow_enabled = false
	var sd := OS.get_environment("GROUND_SHADOWDIST")
	if sd != "":
		sun_node.directional_shadow_max_distance = float(sd)
	if OS.get_environment("GROUND_ORTHOSHADOW") == "1":
		sun_node.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
		sun_node.directional_shadow_max_distance = 80.0
		sun_node.shadow_blur = 0.3
	print("[ground_review] sun.energy=", sun_node.light_energy, " shadow=", sun_node.shadow_enabled,
			" global_basis_z=", sun_node.global_transform.basis.z)

	var probe_v := OS.get_environment("GROUND_PROBE")
	if probe_v != "":
		var probe := stage.get_node_or_null("ReflectionProbe")
		if probe is ReflectionProbe:
			probe.intensity = float(probe_v)
			print("[ground_review] probe.intensity -> ", probe.intensity)

	var aster := stage.get_node_or_null("CharacterAster")
	if aster is Node3D and not overview:
		aster.rotation.y = deg_to_rad(-115.0)   # 东南偏东 3/4 面位: 面向镜头且东东北阳光照亮脸侧

	# 灯杆中部的交通凸面镜在 2K 远景读作悬空红环伪影, 评审图内隐藏 (非地面评审范围道具)
	var mirror := stage.find_child("Traffic_Mirror_Post", true, false)
	if mirror is Node3D:
		mirror.visible = false

	print("[ground_review] scene ready, window=", win.size, " mode=", mode)


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
	var path := OUT_OVERVIEW_PATH if overview else OUT_PATH
	DirAccess.make_dir_absolute(path.get_base_dir())
	var err: Error = img.save_png(path)
	if err == OK:
		print("[ground_review] saved: ", path, " size=", img.get_size())
	else:
		push_error("[ground_review] save failed err=%d" % err)
	get_tree().quit(0 if err == OK else 1)
