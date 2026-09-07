extends SceneTree

## 真机 2K 评审截图（窗口化运行，禁止 --headless）：
##   godot --path client-godot-v2 -s tests/combat_review_capture.gd
## ① aster_locomotion_sprint_review.png：疾跑侧面机位（双鞋独立/长发飘起/摆臂前倾）
## ② aster_combat_combo_slash_review.png：太刀大展开挥砍 + 月华带状刀光
## 布光铁律：卸下 playground 内联环境，换装 endfield_lighting_studio + endfield_studio_environment。

## 候选帧全部落临时目录，人眼挑选后仅两张终审图入 art/render_previews/combat/
const OUT_DIR := "C:/Users/TimeCraker/AppData/Local/Temp/aster_pipeline/captures"

var player: PlayerController = null
var rig: AsterRig = null
var fsm: PlayerCombatFSM = null
var review_cam: Camera3D = null
var cam_offset := Vector3(2.9, 1.15, 0.35)
var cam_look_h := 0.95
var cam_fov := 42.0
var images: Dictionary = {}  # name -> Image（内存攒帧，退出统一写盘，避免逐帧写盘卡死渲染）
var treadmill_on: bool = false
var force_speed := 0.0  # >0 时每物理帧强制该水平速度（扫描混合步态用）

func _initialize() -> void:
	root.size = Vector2i(2048, 1152)  # SceneTree 脚本无 get_window()，root 即 Window
	var scene_res: PackedScene = load("res://scenes/levels/combat_playground.tscn")
	var scene: Node = scene_res.instantiate()
	root.add_child(scene)
	_main(scene)

func _main(scene: Node) -> void:
	await ticks(2)  # 等 READY 传播完成，@onready 节点就绪
	# 场景加载会把窗口尺寸重置回项目设置，必须在其后重新断言 2K 规格分辨率
	root.mode = Window.MODE_WINDOWED
	root.size = Vector2i(2048, 1152)
	await ticks(2)
	print("[capture] window size after re-assert = ", root.size)
	player = scene.get_node("Player")
	rig = player.visual_root.get_node("CharacterAster")
	fsm = player.combat_fsm
	_swap_to_endfield_lighting(scene)

	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))
	await _capture_flow()

func _swap_to_endfield_lighting(scene: Node) -> void:
	var studio: Node3D = (load("res://scenes/lighting/endfield_lighting_studio.tscn") as PackedScene).instantiate()
	scene.add_child(studio)
	# 停用 playground 内联环境与阳光，统一走 endfield 标准（AgX4 / 曝光1.0 / 太阳1.1）
	var old_we: WorldEnvironment = scene.get_node_or_null("WorldEnvironment")
	if old_we:
		old_we.environment = load("res://environments/endfield_studio_environment.tres")
	var old_sun: DirectionalLight3D = scene.get_node_or_null("DirectionalLight3D")
	if old_sun:
		old_sun.visible = false
	var hud: Node = scene.get_node_or_null("HUDLayer")
	if hud:
		hud.visible = false
	# 隐藏关卡白模调试文字（Label3D 区域标牌），保持评审画面纯净
	for lbl in scene.find_children("*", "Label3D", true, false):
		(lbl as Label3D).visible = false
	# 接管渲染相机：禁用运镜控制器处理，评审相机固定机位
	player.camera_controller.process_mode = Node.PROCESS_MODE_DISABLED

func _treadmill(delta: float) -> void:
	if not treadmill_on or player == null:
		return
	# 跑步机锁位：贴地 y=0.001（悬空会误入 FALL 滞空）
	# 每物理帧传送必须复位物理插值，否则 GPU 蒙皮与节点变换时序错位会把网格撕成碎片
	player.global_position = Vector3(0.0, 0.001, 6.0)
	player.reset_physics_interpolation()

func _physics_process(delta: float) -> bool:
	_treadmill(delta)
	if force_speed > 0.0 and player:
		player.velocity = Vector3(0, 0, -force_speed)
	return false

func ticks(n: int) -> void:
	for i in n:
		await physics_frame

func snap(name: String) -> void:
	# 相机跟随玩家重摆（锁位与节点物理存在次序差，逐帧跟随消除构图漂移）
	review_cam.global_position = player.global_position + cam_offset
	review_cam.look_at(player.global_position + Vector3(0, cam_look_h, 0))
	# 诊断：状态/树节点/混合值/髋部世界高
	var hip_w: Vector3 = rig.skeleton.global_transform * rig.skeleton.get_bone_global_pose(rig.skeleton.find_bone("Hip")).origin
	print("[snap %s] fsm=%d tree=%s blend=%.2f hipY=%.2f pos=%s drawn=%s" % [
		name, fsm.current_state, rig.get_current_state_node(),
		rig.anim_tree.get("parameters/SM/Locomotion/blend_position"),
		hip_w.y, str(player.global_position.snapped(Vector3(0.1, 0.1, 0.1))), rig.is_drawn])
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	images[name] = img

func _place_review_cam(offset: Vector3, look_height: float, fov: float) -> void:
	cam_offset = offset
	cam_look_h = look_height
	cam_fov = fov
	if review_cam == null:
		review_cam = Camera3D.new()
		review_cam.name = "ReviewCamera"
		root.add_child(review_cam)
	review_cam.global_position = player.global_position + offset
	review_cam.look_at(player.global_position + Vector3(0, look_height, 0))
	review_cam.fov = fov
	review_cam.make_current()

func _capture_flow() -> void:
	# ---------- 阶段 0：三态对照诊断（idle/walk/sprint 同机位） ----------
	await ticks(10)
	player.global_position = Vector3(0.0, 0.001, 6.0)
	player.visual_root.rotation = Vector3.ZERO
	treadmill_on = true
	_place_review_cam(Vector3(2.9, 1.15, 0.35), 0.95, 42.0)
	await ticks(40)
	await snap("diag_blend0")
	player.velocity = Vector3(0, 0, -2.8)
	await ticks(50)
	await snap("diag_blend28")
	player.velocity = Vector3(0, 0, -7.0)
	await ticks(50)
	await snap("diag_blend70")

	# ---------- 阶段 1：疾跑侧面 ----------
	await ticks(10)
	player.global_position = Vector3(0.0, 0.001, 6.0)
	player.rotation = Vector3.ZERO
	player.visual_root.rotation = Vector3.ZERO
	# 全身机位：包含头部与完整步幅
	_place_review_cam(Vector3(2.7, 1.35, 0.40), 1.05, 40.0)
	# 纯 Sprint 扫描：blend=7.0 直取 LightRunning 原剪辑，30 帧覆盖整周期细相位
	for sweep in [[7.0, "sprint"], [5.0, "run"]]:
		force_speed = sweep[0]
		await ticks(60)  # 收敛进稳定循环
		for i in 30:
			await snap("%s_cand_%02d" % [sweep[1], i])
			await ticks(2)
	force_speed = 0.0
	Input.action_release("sprint")
	Input.action_release("move_forward")
	treadmill_on = false

	# ---------- 阶段 2：太刀连招 ----------
	await ticks(30)
	player.global_position = Vector3(0.0, 0.001, 6.0)
	player.velocity = Vector3.ZERO
	fsm.change_state(PlayerCombatFSM.State.IDLE)
	await ticks(20)  # 回归 idle 稳定
	_place_review_cam(Vector3(2.0, 1.5, -2.4), 1.05, 46.0)  # 侧前方 3/4 机位
	# 四段连招：每段 >0.2s 消耗缓冲推进，Slash3(1.79s) 为大开大合主段
	fsm.buffer_input("attack")
	await ticks(20)
	fsm.buffer_input("attack")
	await ticks(20)
	fsm.buffer_input("attack")
	print("stage3 window: capturing...")
	for i in 14:
		await snap("slash_cand_%02d" % i)
		await ticks(4)
	# 第 4 段 Uppercut 也抓几帧（收势大升龙体态）
	fsm.buffer_input("attack")
	await ticks(14)
	for i in 6:
		await snap("slash_cand_u_%02d" % i)
		await ticks(4)

	# ---------- 统一写盘 ----------
	for name: String in images:
		var img: Image = images[name]
		img.save_png(ProjectSettings.globalize_path("%s/%s.png" % [OUT_DIR, name]))
	print("CAPTURE_DONE count=%d" % images.size())
	quit(0)
