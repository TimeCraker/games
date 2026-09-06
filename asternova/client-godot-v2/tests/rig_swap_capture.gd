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
		# ============ 打击手感数值验证：磁性吸附 + 卡肉顿帧 + 震屏 ============
		170:
			# 传送到木桩前 2.5m (4.5m 软锁距离内、正前方扇形)
			player.global_position = Vector3(0, 0.1, -2.5)
			player.velocity = Vector3.ZERO
			player.visual_root.rotation.y = 0.0
			player.combat_fsm.change_state(PlayerCombatFSM.State.IDLE)
			pre_lunge_dist = _dummy_dist()
			_hit_min_time_scale = 1.0
		176:
			# 确认已落地回正再出刀，防止缓冲被空中星坠抢走
			_check("落定进入待命", player.is_on_floor() and player.combat_fsm.current_state == PlayerCombatFSM.State.IDLE)
			player.combat_fsm.buffer_input("attack")
		177:
			_hit_min_time_scale = minf(_hit_min_time_scale, Engine.time_scale)
		178:
			_hit_min_time_scale = minf(_hit_min_time_scale, Engine.time_scale)
		179:
			_hit_min_time_scale = minf(_hit_min_time_scale, Engine.time_scale)
		182:
			_check("卡肉顿帧触发 (time_scale<1)", _hit_min_time_scale < 1.0)
			_check("震屏 trauma>0.1", player.camera_controller.trauma > 0.1)
			_check("木桩受击", _dummy().hit_count >= 1)
		192:
			var closed: float = pre_lunge_dist - _dummy_dist()
			_check("磁性吸附前突 0.3~0.5m (实测 %.2fm)" % closed, closed > 0.25 and closed < 0.55)
			_snap("calib_09_magnetic_lunge_hit.png")
			print("--- 真身标定实跑完成 ---")
			get_tree().quit(0)

var pre_lunge_dist: float = 0.0
var _hit_min_time_scale: float = 1.0

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
