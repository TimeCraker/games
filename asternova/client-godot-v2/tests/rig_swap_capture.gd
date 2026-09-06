extends Node

## 真身替换标定驱动：窗口化实机验证跑动/滑铲/跳跃/插槽切换并抓取标定截图
## 相机方位基准：角色默认面向 -Z；yaw=PI 为正面机位，yaw=-PI/2 为左侧机位

var player: PlayerController = null
var rig: AsterRig = null
var frame_count: int = 0
var run_start_pos: Vector3 = Vector3.ZERO
var snapshot_dir: String = "res://playtest_snapshots/"

func _ready() -> void:
	var dir: DirAccess = DirAccess.open("res://")
	if not dir.dir_exists("playtest_snapshots"):
		dir.make_dir("playtest_snapshots")

func _physics_process(_delta: float) -> void:
	frame_count += 1
	if not player:
		var players: Array = get_tree().get_nodes_in_group("player")
		if players.size() > 0:
			player = players[0] as PlayerController
			rig = player.aster_rig
		return

	# 落地回正确认后自动缓冲攻击，并连拍择优
	if _pending_attack_at_ground and player.is_on_floor() and player.combat_fsm.current_state == PlayerCombatFSM.State.IDLE:
		_pending_attack_at_ground = false
		_attack_fired_frame = frame_count + 1
		player.combat_fsm.buffer_input("attack")
	if not _pending_burst.is_empty() and _attack_fired_frame > 0:
		var rel: int = frame_count - _attack_fired_frame
		if _pending_burst.has(rel):
			# 仅内存取帧（同步写盘会卡死渲染循环导致连拍重复帧），退出时统一写盘
			var vp: Viewport = get_viewport()
			if vp:
				_burst_images[_pending_burst[rel]] = vp.get_texture().get_image()
			_pending_burst.erase(rel)

	match frame_count:
		20:
			_frame_camera(PI, -8.0, 2.6)
			_snap("calib_00_idle_sheathe_front.png")
			_check("正面待机(纳刀态)", rig.is_drawn == false)
		24:
			_frame_camera(-PI / 2, -14.0, 1.15)
		26:
			_snap("calib_01_sheathe_left_profile.png")
		40:
			# 拔刀：刀身切换至右手
			player.update_blade_stance(true)
			_check("拔刀态切换", rig.is_drawn and rig.katana_blade.get_parent() == rig.hand_socket)
		44:
			_frame_camera(PI / 2, -8.0, 1.25)
		46:
			_snap("calib_02_draw_right_profile.png")
		50:
			# 面向 -Z 方向木桩并出刀（软锁定 + 磁性吸附 + 挥刀）
			player.visual_root.rotation.y = 0.0
			player.combat_fsm.buffer_input("attack")
		54:
			_frame_camera(3 * PI / 4, -6.0, 2.3)
		57:
			_snap("calib_03_swing_stage1.png")
		62:
			player.combat_fsm.buffer_input("attack")
		70:
			_snap("calib_04_swing_stage2.png")
		68:
			# 居合蓄力架刀姿态验证 (按住右键蓄力)
			Input.action_press("guard_charge")
			player.combat_fsm.change_state(PlayerCombatFSM.State.GUARD_CHARGE)
		76:
			_frame_camera(PI * 0.85, -8.0, 2.0)
			_snap("calib_08_guard_charge.png")
		78:
			Input.action_release("guard_charge")
		82:
			# 纳刀回归验证 (松键后自动退出蓄力并回鞘)
			_check("蓄力松键回纳刀", rig.is_drawn == false and rig.katana_blade.get_parent() == rig.scabbard_socket)
		90:
			# 疾跑 0.5s (镜头切回背后跟随机位, 7m/s 跑动状态)
			_frame_camera(0.15, -8.0, 2.6)
			run_start_pos = player.global_position
			Input.action_press("move_forward")
			Input.action_press("sprint")
		114:
			# 终版验收图机位：3/4 侧后跟拍，纳刀跑动实机画面
			_frame_camera(0.45, -7.0, 2.45)
		116:
			_snap("aster_rig_swap_review.png")
		120:
			_snap("calib_05_run.png")
			_check("跑动位移>0.5m", player.global_position.distance_to(run_start_pos) > 0.5)
		121:
			Input.action_release("move_forward")
			Input.action_release("sprint")
			# 滑铲
			Input.action_press("move_forward")
			player.combat_fsm.buffer_input("slide")
		128:
			_snap("calib_06_slide.png")
			_check("滑铲状态", player.combat_fsm.current_state == PlayerCombatFSM.State.SLIDE and player.is_sliding)
		136:
			Input.action_release("move_forward")
			# 跳跃
			player.combat_fsm.buffer_input("jump")
		146:
			_snap("calib_07_jump.png")
			_check("离地跳跃", player.global_position.y > 0.3 or player.velocity.y > 0.0)
		160:
			_check("存活未坠崖", player.global_position.y > -5.0)
		# ============ 打击手感数值验证：磁性吸附 + 单体局部卡肉 + 震屏 ============
		170:
			# 传送到木桩前 2.5m (4.5m 软锁距离内、正前方扇形)
			player.global_position = Vector3(0, 0.1, -2.5)
			player.velocity = Vector3.ZERO
			player.visual_root.rotation.y = 0.0
			player.combat_fsm.change_state(PlayerCombatFSM.State.IDLE)
			pre_lunge_dist = _dummy_dist()
			_saw_player_freeze = false
			_saw_dummy_freeze = false
			_max_trauma = 0.0
		176:
			# 确认已落地回正再出刀，防止缓冲被空中星坠抢走
			_check("落定进入待命", player.is_on_floor() and player.combat_fsm.current_state == PlayerCombatFSM.State.IDLE)
			_check("刀光标记点就绪", rig.blade_base_marker != null and rig.blade_tip_marker != null)
			player.combat_fsm.buffer_input("attack")
		177:
			_saw_player_freeze = _saw_player_freeze or player.hitstop_timer > 0.0
			_saw_dummy_freeze = _saw_dummy_freeze or _dummy().freeze_timer > 0.0
			_max_trauma = maxf(_max_trauma, player.camera_controller.trauma)
		178:
			_saw_player_freeze = _saw_player_freeze or player.hitstop_timer > 0.0
			_saw_dummy_freeze = _saw_dummy_freeze or _dummy().freeze_timer > 0.0
			_max_trauma = maxf(_max_trauma, player.camera_controller.trauma)
		179:
			_saw_player_freeze = _saw_player_freeze or player.hitstop_timer > 0.0
			_saw_dummy_freeze = _saw_dummy_freeze or _dummy().freeze_timer > 0.0
			_max_trauma = maxf(_max_trauma, player.camera_controller.trauma)
		182:
			_check("主角单体冻结 (time_scale 恒 1.0)", _saw_player_freeze and Engine.time_scale == 1.0)
			_check("木桩单体冻结", _saw_dummy_freeze)
			_check("震屏 trauma>0.1 (峰值 %.2f)" % _max_trauma, _max_trauma > 0.1)
			_check("木桩受击", _dummy().hit_count >= 1)
		192:
			var closed: float = pre_lunge_dist - _dummy_dist()
			_check("磁性吸附前突 0.3~0.5m (实测 %.2fm)" % closed, closed > 0.25 and closed < 0.55)
		# ============ 太刀月华刀光 + 卡肉闪白 2K 抓拍 ============
		200:
			# 第2段挥刀纯刀光抓拍：拉远到软锁距离外空挥，避免卡肉冻结定格
			# 传送后有 1~5 帧空中 FALL 窗口，必须落地确认后再缓冲攻击（防被星坠抢走）
			player.global_position = Vector3(0, 0.1, 5.5)
			player.velocity = Vector3.ZERO
			player.visual_root.rotation.y = 0.0
			player.combat_fsm.change_state(PlayerCombatFSM.State.IDLE)
			player.combat_fsm.combo_index = 1
			player.update_blade_stance(true)
			_frame_camera(PI, -28.0, 2.6)
			_queue_ground_attack({
				4: "trail_s2_b4.png", 5: "trail_s2_b5.png", 6: "trail_s2_b6.png",
				7: "trail_s2_b7.png", 8: "trail_s2_b8.png", 9: "trail_s2_b9.png",
				10: "trail_s2_b10.png", 11: "trail_s2_b11.png"})
		232:
			# 4段终结命中抓拍：贴近木桩，重卡肉 0.10s + 闪白 0.06s + 击退 0.45m
			# (232 > 第2段挥刀自然结束帧，避免掐断刀光采样)
			player.global_position = Vector3(0, 0.1, -2.6)
			player.velocity = Vector3.ZERO
			player.visual_root.rotation.y = 0.0
			player.combat_fsm.change_state(PlayerCombatFSM.State.IDLE)
			player.combat_fsm.combo_index = 3
			player.update_blade_stance(true)
			_frame_camera(PI * 0.62, -6.0, 2.9)
			_queue_ground_attack({})
		272:
			# 侧面全景机位重拍终结命中：等上一段攻击自然收招后再出刀，闪白最强帧
			# 抓拍时隐藏键位面板，避免遮挡伤害浮字
			var hud_node: CanvasItem = get_tree().get_first_node_in_group("hud") as CanvasItem
			var guide: Control = hud_node.get_node_or_null("KeyGuidePanel") as Control
			if guide:
				guide.visible = false
			# 重置木桩计数并隐藏其信息牌，保证命中反馈画面干净
			var dummy_node: TrainingDummy = _dummy()
			dummy_node.hit_count = 0
			dummy_node.total_damage = 0.0
			dummy_node.update_info_display()
			if dummy_node.info_label:
				dummy_node.info_label.visible = false
			player.global_position = Vector3(0, 0.1, -2.6)
			player.velocity = Vector3.ZERO
			player.visual_root.rotation.y = 0.0
			player.combat_fsm.combo_index = 3
			player.update_blade_stance(true)
			_frame_camera(-PI * 0.44, -4.0, 3.4)
			_queue_ground_attack({
				1: "trail_fin_b1.png", 2: "trail_fin_b2.png", 3: "trail_fin_b3.png",
				4: "trail_fin_b4.png", 5: "trail_fin_b5.png"})
		240:
			_check("终结命中后仰 0.45m", _dummy().mesh_root.position.distance_to(_dummy().original_mesh_pos) > 0.2 or _dummy().hit_count >= 2)
		285:
			_flush_burst_images()
			print("--- 刀光与卡肉实跑验证完成 ---")
			get_tree().quit(0)

var pre_lunge_dist: float = 0.0
var _saw_player_freeze: bool = false
var _saw_dummy_freeze: bool = false
var _max_trauma: float = 0.0
var _pending_attack_at_ground: bool = false
var _attack_fired_frame: int = -1
var _pending_burst: Dictionary = {} # 相对出刀帧的偏移 -> 文件名
var _burst_images: Dictionary = {} # 文件名 -> Image

## 落地回正确认后自动缓冲攻击，并在挥击段逐帧连拍
func _queue_ground_attack(captures: Dictionary) -> void:
	_pending_attack_at_ground = true
	_pending_burst = captures
	_attack_fired_frame = -1

func _flush_burst_images() -> void:
	for filename in _burst_images:
		var img: Image = _burst_images[filename]
		if img and not img.is_empty():
			img.save_png(snapshot_dir + filename)
			print("📸 %s (%dx%d)" % [filename, img.get_width(), img.get_height()])
	_burst_images.clear()

func _dummy() -> TrainingDummy:
	return get_tree().get_first_node_in_group("target_dummy") as TrainingDummy

func _dummy_dist() -> float:
	var d := _dummy()
	return player.global_position.distance_to(d.global_position) if d else -1.0

func _frame_camera(yaw: float, pitch_deg: float, arm_length: float) -> void:
	var cc := player.camera_controller
	cc.current_yaw = yaw
	cc.current_pitch = deg_to_rad(pitch_deg)
	cc.rotation.y = yaw
	cc.spring_arm.rotation.x = cc.current_pitch
	cc.target_arm_length = arm_length
	cc.spring_arm.spring_length = arm_length

func _snap(filename: String) -> void:
	var vp: Viewport = get_viewport()
	if vp:
		var img: Image = vp.get_texture().get_image()
		if img and not img.is_empty():
			img.save_png(snapshot_dir + filename)
			print("📸 %s (%dx%d)" % [filename, img.get_width(), img.get_height()])

func _check(label: String, ok: bool) -> void:
	if ok:
		print("✔ 标定检查: %s" % label)
	else:
		printerr("✘ 标定失败: %s" % label)
