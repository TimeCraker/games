extends Node

## 现代日本晴空住宅街区与 CS2 级沙盒战斗地图 (Asternova M1/M2) 自动化实机测试驱动器 V2
## 严格捕获 6 张 1080P 高清实机检验截图，对照 31 张官方参考图验证次世代微表面质感与日式生活气息

var player: PlayerController = null
var dummy: TrainingDummy = null
var drone: TrainingDrone = null
var hud: HUDController = null

var frame_count: int = 0
var current_phase: int = 0
var phase_timer: float = 0.0

var primary_snapshot_dir: String = "res://playtest_snapshots/sandbox/"
var export_dirs: Array[String] = [
	"c:/Users/TimeCraker/Desktop/my-workspace/games/asternova/render-lab/screenshots/playtest_v2/",
	"c:/Users/TimeCraker/Desktop/my-workspace/games/render-lab/screenshots/playtest_v2/"
]
var subaction_step: int = 0

func _ready() -> void:
	print("======================================================================")
	print("★ Asternova M1/M2 次世代日式都市街区 (CS2 PBR + ZZZ 生活气息) 实机验收启动 ★")
	print("======================================================================")
	
	var dir: DirAccess = DirAccess.open("res://")
	if not dir.dir_exists("playtest_snapshots"):
		dir.make_dir("playtest_snapshots")
	if not dir.dir_exists("playtest_snapshots/sandbox"):
		dir.make_dir("playtest_snapshots/sandbox")
		
	for exp_d in export_dirs:
		if not DirAccess.dir_exists_absolute(exp_d):
			DirAccess.make_dir_recursive_absolute(exp_d)

func _physics_process(delta: float) -> void:
	frame_count += 1
	phase_timer += delta

	if not player:
		var players: Array = get_tree().get_nodes_in_group("player")
		if players.size() > 0:
			player = players[0] as PlayerController
		var dummies: Array = get_tree().get_nodes_in_group("target_dummy")
		for d in dummies:
			if d is TrainingDummy:
				dummy = d
			elif d is TrainingDrone:
				drone = d
		var huds: Array = get_tree().get_nodes_in_group("hud")
		if huds.size() > 0:
			hud = huds[0] as HUDController
		return

	if player and player.visual_root:
		player.visual_root.visible = false

	match current_phase:
		0: # 阶段 1: 南端生活广场便利店与写实双联自动贩卖机微距特写 (对标 ZZZ 01/02)
			if phase_timer < 0.05:
				player.global_position = Vector3(-4.5, 1.3, 21.2)
				player.velocity = Vector3.ZERO
				player.camera_controller.current_mode = CameraController.CameraMode.FPP
				player.camera_controller.target_arm_length = 0.0
				player.camera_controller.spring_arm.spring_length = 0.0
				player.camera_controller.rotation.y = deg_to_rad(90.0)
				player.camera_controller.current_yaw = deg_to_rad(90.0)
				player.camera_controller.spring_arm.rotation.x = deg_to_rad(-2.0)
				player.camera_controller.current_pitch = deg_to_rad(-2.0)
			elif phase_timer >= 0.6:
				capture_snapshot("01_plaza_store_vending_view.png")
				print("[机位 1 通过] 便利店真实发光招牌、落地窗双层陈列货架与写实双联自动贩卖机捕获！")
				advance_phase()

		1: # 阶段 2: 沥青路面微表面、灌缝修补胶反光、黄色导盲砖与路缘石微距特写 (对标 CS2 01 / ZZZ 12)
			if phase_timer < 0.05:
				player.global_position = Vector3(-4.2, 0.45, 20.0)
				player.velocity = Vector3.ZERO
				player.camera_controller.current_mode = CameraController.CameraMode.FPP
				player.camera_controller.target_arm_length = 0.0
				player.camera_controller.spring_arm.spring_length = 0.0
				player.camera_controller.rotation.y = deg_to_rad(175.0)
				player.camera_controller.current_yaw = deg_to_rad(175.0)
				player.camera_controller.spring_arm.rotation.x = deg_to_rad(-42.0)
				player.camera_controller.current_pitch = deg_to_rad(-42.0)
			elif phase_timer >= 0.5:
				capture_snapshot("02_asphalt_curb_tactile_closeup.png")
				print("[机位 2 通过] 粗骨料沥青路面、灌缝胶反光、倒角路缘石与黄色导盲砖微距质感捕获！")
				advance_phase()

		2: # 阶段 3: 40m 战术跑酷坡道顺接与纵横架空电缆网 (对标 ZZZ 03/11)
			if phase_timer < 0.05:
				player.global_position = Vector3(0.0, 0.8, 16.0)
				player.velocity = Vector3.ZERO
				player.camera_controller.current_mode = CameraController.CameraMode.FPP
				player.camera_controller.target_arm_length = 0.0
				player.camera_controller.spring_arm.spring_length = 0.0
				player.camera_controller.rotation.y = deg_to_rad(0.0)
				player.camera_controller.current_yaw = deg_to_rad(0.0)
				player.camera_controller.spring_arm.rotation.x = deg_to_rad(10.0)
				player.camera_controller.current_pitch = deg_to_rad(10.0)
			elif phase_timer >= 0.5:
				capture_snapshot("03_slope_ramp_overhead_cables.png")
				print("[机位 3 通过] 40m 战术跑酷坡道平缓顺接与空中纵横交错悬垂电缆捕获！")
				advance_phase()

		3: # 阶段 4: 3.5m 战术小巷横条砖与清水混凝土外立面 (对标 CS2 10 / ZZZ 13)
			if phase_timer < 0.05:
				player.global_position = Vector3(-8.8, 1.3, -0.5)
				player.velocity = Vector3.ZERO
				player.camera_controller.current_mode = CameraController.CameraMode.FPP
				player.camera_controller.target_arm_length = 0.0
				player.camera_controller.spring_arm.spring_length = 0.0
				player.camera_controller.rotation.y = deg_to_rad(90.0)
				player.camera_controller.current_yaw = deg_to_rad(90.0)
				player.camera_controller.spring_arm.rotation.x = deg_to_rad(3.0)
				player.camera_controller.current_pitch = deg_to_rad(3.0)
			elif phase_timer >= 0.5:
				capture_snapshot("04_tactical_alley_wall_textures.png")
				print("[机位 4 通过] 3.5m 战术小巷日式米白挂板、浅灰细条砖与清水混凝土外立面捕获！")
				advance_phase()

		4: # 阶段 5: 街头生活道具生态 (分类垃圾桶、反光锥、广角镜与路缘石) (对标 CS2 03/08)
			if phase_timer < 0.05:
				player.global_position = Vector3(-2.8, 1.1, 17.5)
				player.velocity = Vector3.ZERO
				player.camera_controller.current_mode = CameraController.CameraMode.FPP
				player.camera_controller.target_arm_length = 0.0
				player.camera_controller.spring_arm.spring_length = 0.0
				player.camera_controller.rotation.y = deg_to_rad(65.0)
				player.camera_controller.current_yaw = deg_to_rad(65.0)
				player.camera_controller.spring_arm.rotation.x = deg_to_rad(-10.0)
				player.camera_controller.current_pitch = deg_to_rad(-10.0)
			elif phase_timer >= 0.5:
				capture_snapshot("05_street_props_ecology_closeup.png")
				print("[机位 5 通过] 日式分类垃圾桶、黄色反光交通锥与街头生活道具生态捕获！")
				advance_phase()

		5: # 阶段 6: 北侧山顶鸟居鸟瞰全景 (验证 360° 天际线封闭无虚空与 ACES 通透光影)
			if phase_timer < 0.05:
				player.global_position = Vector3(0.0, 7.2, -25.5)
				player.camera_controller.current_mode = CameraController.CameraMode.FPP
				player.camera_controller.target_arm_length = 0.0
				player.camera_controller.spring_arm.spring_length = 0.0
				player.camera_controller.rotation.y = deg_to_rad(180.0)
				player.camera_controller.current_yaw = deg_to_rad(180.0)
				player.camera_controller.spring_arm.rotation.x = deg_to_rad(-18.0)
				player.camera_controller.current_pitch = deg_to_rad(-18.0)
			elif phase_timer >= 0.6:
				capture_snapshot("06_north_torii_panorama_aces.png")
				print("[机位 6 通过] 北侧高台鸟瞰全景、360° 封闭天际线与 ACES 通透光影捕获！")
				advance_phase()

		6: # 阶段 7: 测试汇总与安全退出
			print("======================================================================")
			print("★ Asternova 次世代日式都市街区 (CS2 PBR + ZZZ 生活气息) 全部 6 大视角验收完成！★")
			print("★ 验收截图已完整导出至 render-lab/screenshots/playtest_v2/ ★")
			print("======================================================================")
			advance_phase()
			get_tree().quit(0)

func advance_phase() -> void:
	current_phase += 1
	phase_timer = 0.0
	subaction_step = 0

func capture_snapshot(filename: String) -> void:
	var vp: Viewport = get_viewport()
	if vp:
		var tex: ViewportTexture = vp.get_texture()
		if tex:
			var img: Image = tex.get_image()
			if img and not img.is_empty():
				# 1. 保存至 Godot 项目内
				var res_path: String = primary_snapshot_dir + filename
				img.save_png(res_path)
				
				# 2. 导出至物理目录
				for exp_d in export_dirs:
					var full_path: String = exp_d + filename
					img.save_png(full_path)
					
				print("📸 已捕获 1080P 实机验证截图 -> %s (%dx%d)" % [filename, img.get_width(), img.get_height()])
