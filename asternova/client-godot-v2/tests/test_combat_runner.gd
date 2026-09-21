extends SceneTree

## 自动化战斗门禁：场景完整性 + 动捕动画系统 + 移动混合 + 四段连招 + 拔刀联动 + 局部卡肉
## + 顺切线受击推力刹停与白闪 + 星闪·时空断裂局部时停
## 运行： godot --headless --path client-godot-v2 -s tests/test_combat_runner.gd

var tick: int = 0
var scene: Node = null
var phase: String = "boot"
var player: PlayerController = null
var rig: AsterRig = null
var fsm: PlayerCombatFSM = null
var driver: AsterAnimDriver = null
var check_total: int = 0

# 连招测试状态
var combo_round: int = 0
var combo_seen: Array[int] = []
var _bone_pose_before: Quaternion = Quaternion.IDENTITY
var _failures: Array[String] = []

# 受击推力与星闪测试状态
var kb_dummy: TrainingDummy = null
var bt_drone: TrainingDrone = null
var _kb_offset_light: Vector3 = Vector3.ZERO
var _dash_start_pos: Vector3 = Vector3.ZERO
var _drone_snap_timer: float = 0.0
var _drone_snap_pos: Vector3 = Vector3.ZERO

func check(cond: bool, msg: String) -> void:
	check_total += 1
	if cond:
		print("  ✔ " + msg)
	else:
		_failures.append(msg)
		printerr("  ✘ FAIL: " + msg)

func _initialize() -> void:
	print("--- 开始自动化战斗沙盒加载与完整性测试 ---")
	var scene_res: PackedScene = load("res://scenes/levels/combat_playground.tscn")
	if not scene_res:
		printerr("FAIL: 无法加载 combat_playground.tscn")
		quit(1)
		return
	scene = scene_res.instantiate()
	root.add_child(scene)

func _physics_process(_delta: float) -> bool:
	tick += 1
	match phase:
		"boot":
			if tick >= 4:
				phase_integrity()
				if _failures.is_empty():
					phase = "anim_ready"
					_anim_capture_before()
			return _maybe_quit()
		"anim_ready":
			phase_anim_ready()
			return _maybe_quit()
		"mocap_driving":
			phase_mocap_driving()
			return _maybe_quit()
		"locomotion_blend":
			phase_locomotion_blend()
			return _maybe_quit()
		"combo_chain":
			phase_combo_chain()
			return _maybe_quit()
		"combo_tail":
			phase_combo_tail()
			return _maybe_quit()
		"hitstop":
			phase_hitstop()
			return _maybe_quit()
		"knockback":
			phase_knockback()
			return _maybe_quit()
		"bullet_time":
			phase_bullet_time()
			return _maybe_quit()
		"weapon_mount":
			phase_weapon_mount()
			return _maybe_quit()
	return false

func _maybe_quit() -> bool:
	if not _failures.is_empty():
		printerr("--- 门禁未通过：%d 项失败 ---" % _failures.size())
		quit(1)
		return true
	if phase == "done":
		print("--- 全部 %d 项自动化测试 100%% 通过！---" % check_total)
		quit(0)
		return true
	return false

## ================= 阶段 A：场景完整性（沿用原门禁） =================
func phase_integrity() -> void:
	player = scene.get_node_or_null("Player") as PlayerController
	if not player:
		printerr("FAIL: 场景中未找到 PlayerController")
		quit(1)
		return
	print("✔ PlayerController 存在且就绪")

	rig = player.visual_root.get_node_or_null("CharacterAster") as AsterRig
	check(rig != null, "Aster 真身 rig 不存在")
	check(rig.skeleton != null and (rig.skeleton.get_bone_count() == 43 or rig.skeleton.get_bone_count() == 55), "Aster 骨骼数量异常")
	check(rig.hand_socket != null and rig.hand_socket is BoneAttachment3D, "Hand_R_Weapon_Socket 插槽缺失")
	check(rig.scabbard_socket != null and rig.scabbard_socket is BoneAttachment3D, "Pelvis_L_Scabbard_Socket 插槽缺失")
	check(rig.katana_blade != null, "Katana_Blade 刀身网格缺失")
	print("✔ Aster 真身 rig 就绪: %d 骨骼 / 双插槽 / 刀身网格齐备" % rig.skeleton.get_bone_count())

	check(not rig.is_drawn, "入场默认应为纳刀态")
	check(rig.katana_blade.get_parent() == rig.scabbard_socket, "纳刀态刀身未挂在左腰鞘插槽")
	rig.draw_sword()
	check(rig.is_drawn and rig.katana_blade.get_parent() == rig.hand_socket, "拔刀后刀身未切换至右手插槽")
	rig.sheathe_sword()
	check(not rig.is_drawn and rig.katana_blade.get_parent() == rig.scabbard_socket, "纳刀回鞘失败")
	print("✔ 拔刀/纳刀双插槽切换检验通过 (Hand_R ↔ Pelvis_L_Scabbard)")

	var body_mi: MeshInstance3D = rig.skeleton.get_node_or_null("Aster_Body") as MeshInstance3D
	check(body_mi != null, "Aster_Body 网格缺失")
	var body_mat: Material = body_mi.get_surface_override_material(0)
	check(body_mat is ShaderMaterial and (body_mat as ShaderMaterial).shader != null, "Aster_Body 未实装着色器材质")
	print("✔ NPR toon+outline 着色实装检验通过")

	var capsule: CapsuleShape3D = player.collision_shape.shape as CapsuleShape3D
	check(capsule != null, "碰撞体不是胶囊体")
	check(is_equal_approx(capsule.radius, 0.38), "胶囊半径应为 0.38m")
	check(is_equal_approx(capsule.height, 1.65), "胶囊高度应为 1.65m")
	check(is_equal_approx(player.collision_shape.position.y, 0.825), "胶囊中心高应为 0.825m")
	print("✔ 真身胶囊碰撞体校验通过: r=0.38 h=1.65 c=0.825")

	var cd: CombatData = player.combat_data
	check(cd != null, "CombatData 为空")
	check(is_equal_approx(cd.walk_speed, 2.8), "walk 标定移速应为 2.8 m/s（动捕剪辑标定）")
	check(is_equal_approx(cd.sprint_speed, 7.0), "run 标定移速应为 7.0 m/s")
	check(cd.combo_anim_lengths.size() == 4, "四段连招动捕时长表缺失")
	check(is_equal_approx(cd.iai_release_length, 1.333), "居合释放时长应为 SlashRelease 剪辑长度")
	print("✔ CombatData 校验通过: walk=%.1f, sprint=%.1f, 连招时长=%s" % [
		cd.walk_speed, cd.sprint_speed, str(cd.combo_anim_lengths)])
	check(cd.slide_initial_speed == 12.0 and cd.slide_jump_momentum_keep == 0.90, "滑铲参数异常")
	check(cd.plunge_speed == 24.0 and cd.max_wall_jumps == 3, "立体机动参数异常")
	check(cd.parry_window == 0.15, "弹刀窗口应为 0.15s")
	check(cd.hitstop_stage_freeze[3] == 0.10 and cd.hitstop_iaijutsu == 0.15, "卡肉分级参数异常")
	check(cd.magnetic_lunge_distance == 0.4 and cd.magnetic_lunge_cone_deg == 45.0, "磁性吸附参数异常")
	print("✔ 分级单体卡肉与磁性索敌参数校验通过")

	var hud: HUDController = scene.get_node_or_null("HUDLayer/HUD") as HUDController
	check(hud != null, "HUDLayer/HUD 未找到")

	var dummies: Array = get_nodes_in_group("target_dummy")
	check(dummies.size() >= 2, "靶子数量不足 2 个")
	print("✔ 发现靶子数量: %d 个" % dummies.size())

	check(scene.has_node("Zone1_Combat") and scene.has_node("Zone2_Slope")
		and scene.has_node("Zone3_Vertical") and scene.has_node("Zone4_WallBounce")
		and scene.has_node("Zone5_Drone"), "特色地貌区域缺失")
	print("✔ 全部 5 大核心战斗与跑酷地貌检验通过")

	var dummy: TrainingDummy = scene.get_node_or_null("Zone1_Combat/TrainingDummy") as TrainingDummy
	check(dummy != null, "TrainingDummy 未找到")
	if dummy:
		dummy.take_hit(25.0, Vector3.FORWARD, false)
		check(dummy.hit_count == 1 and dummy.total_damage == 25.0, "木桩受击结算异常")
	var drone: TrainingDrone = scene.get_node_or_null("Zone5_Drone/TrainingDrone") as TrainingDrone
	check(drone != null, "TrainingDrone 未找到")
	if drone:
		drone.take_hit(50.0, Vector3.FORWARD, true)
		check(drone.total_damage_taken == 50.0, "傀儡受击结算异常")
	print("✔ 木桩与傀儡受击机制正常")

	player.camera_controller.toggle_camera_mode()
	check(player.camera_controller.current_mode == CameraController.CameraMode.FPP and not rig.visible, "FPP 切换/隐藏真身失败")
	player.camera_controller.toggle_camera_mode()
	check(player.camera_controller.current_mode == CameraController.CameraMode.TPP and rig.visible, "TPP 恢复失败")
	print("✔ FPP/TPP 视角切换检验通过")

## ================= 阶段 B：动捕动画系统 =================
func _anim_capture_before() -> void:
	var idx := rig.skeleton.find_bone("R_Upperarm")
	if idx == -1: idx = rig.skeleton.find_bone("DEF-upper_arm.R")
	_bone_pose_before = rig.skeleton.get_bone_global_pose(idx).basis.get_rotation_quaternion()
	phase = "anim_ready"

func phase_anim_ready() -> void:
	print("--- 动捕动画系统门禁 ---")
	check(rig.anim_player != null, "AnimationPlayer 未创建")
	check(rig.anim_tree != null and rig.anim_tree.active, "AnimationTree 未激活")
	for clip in ["idle", "LightIdle", "LightWalking", "Sprint", "jump", "fall", "fall-landing", "Roll",
			"Slash1", "Slash2", "Slash3", "SlashUppercut", "SlashCharge", "SlashRelease",
			"Guarding", "GuardParry", "wall-slide-front", "HeavyJumpAttack"]:
		check(rig.anim_player.has_animation(clip), "动捕库缺少剪辑: " + clip)
	print("✔ 重定向动捕库挂接完整")

	var pb := rig.anim_tree.get("parameters/SM/playback") as AnimationNodeStateMachinePlayback
	check(pb != null, "状态机 playback 缺失")
	check(String(pb.get_current_node()) == "Locomotion", "入场应处于 Locomotion")
	print("✔ AnimationTree 状态机就绪，当前节点: " + String(pb.get_current_node()))

	# 触发一段真实挥砍，验证骨骼被动捕数据驱动（非 rest 僵直）
	rig.travel("Combo1")
	phase = "mocap_driving"
	tick = 0

func phase_mocap_driving() -> void:
	# 0.25s（15 tick）后 Slash1 已越过 CrossFade 进入蓄力段
	if tick >= 15:
		var idx := rig.skeleton.find_bone("R_Upperarm")
		if idx == -1: idx = rig.skeleton.find_bone("DEF-upper_arm.R")
		var now := rig.skeleton.get_bone_global_pose(idx).basis.get_rotation_quaternion()
		var ang := rad_to_deg(now.angle_to(_bone_pose_before))
		check(ang > 6.0, "骨骼姿态未被动捕数据驱动（上臂变化仅 %.2f°）" % ang)
		print("✔ 动捕数据驱动验证: 上臂姿态变化 %.1f°（挥砍蓄力段）" % ang)
		rig.travel("Locomotion")
		phase = "locomotion_blend"
		tick = 0

## ================= 阶段 C：Locomotion BlendSpace1D =================
func phase_locomotion_blend() -> void:
	if tick == 1:
		fsm = player.combat_fsm
		driver = player.get_node_or_null("AsterAnimDriver") as AsterAnimDriver
		check(driver != null, "AsterAnimDriver 未挂载")
		fsm.change_state(PlayerCombatFSM.State.MOVE)
		# 模拟 7 m/s 疾跑水平速度，驱动器应在下一物理帧写入混合参数
		player.velocity = Vector3(0, 0, -7.0)
	elif tick == 3:
		var blend: float = rig.anim_tree.get("parameters/SM/Locomotion/blend_position")
		check(blend > 5.5, "BlendSpace1D 未被实际速度驱动（blend=%.2f）" % blend)
		check(rig.get_current_state_node() == "Locomotion", "MOVE 态应处于 Locomotion 节点")
		print("✔ Locomotion BlendSpace1D 速度驱动验证: blend=%.2f m/s → run" % blend)
		fsm.change_state(PlayerCombatFSM.State.IDLE)
		phase = "combo_chain"
		tick = 0
		combo_round = 0

## ================= 阶段 D：四段连招 + 拔刀联动 =================
func phase_combo_chain() -> void:
	# 每段间隔 18 tick(0.3s)：缓冲→连招推进（>0.20s 消耗缓冲进下一段）
	if tick == 1 and combo_round < 4:
		fsm.buffer_input("attack")
	if tick == 18:
		tick = 0
		combo_round += 1
		if driver.combo_stage_fired > 0:
			combo_seen.append(driver.combo_stage_fired)
		if combo_round >= 4:
			print("✔ 四段连招推进记录: " + str(combo_seen))
			check(combo_seen.has(1) and combo_seen.has(2) and combo_seen.has(3) and combo_seen.has(4),
				"四段连招未全部打完（记录=%s）" % str(combo_seen))
			check(rig.is_drawn, "连招期间应保持拔刀态")
			check(Engine.time_scale == 1.0, "连招期间全局 time_scale 应恒为 1.0")
			phase = "combo_tail"
			return

func phase_combo_tail() -> void:
	# 等 Combo4 收势 + AT_END 回归 Locomotion（1.375s ≈ 83 tick）
	if tick >= 110:
		check(rig.get_current_state_node() == "Locomotion", "连招结束后应自动回归 Locomotion（当前=%s）" % rig.get_current_state_node())
		check(not rig.is_drawn, "收招后应自动纳刀回鞘")
		check(rig.katana_blade.get_parent() == rig.scabbard_socket, "收招后刀身应归入左腰鞘")
		print("✔ 连招收势自动回归 Locomotion + 纳刀回鞘检验通过")
		phase = "hitstop"
		tick = 0

## ================= 阶段 E：单体局部卡肉 =================
func phase_hitstop() -> void:
	if tick == 1:
		print("--- 单体局部卡肉门禁 ---")
		player.freeze_pose(0.06)
		check(rig.anim_tree.get("parameters/HitstopScale/scale") == 0.0, "卡肉未冻结自身 AnimationTree（HitstopScale!=0）")
		check(Engine.time_scale == 1.0, "卡肉严禁降低全局 Engine.time_scale")
	elif tick == 1 + int(0.1 * 60):
		check(is_equal_approx(rig.anim_tree.get("parameters/HitstopScale/scale"), 1.0), "卡肉计时结束后未恢复播放速度")
		print("✔ 局部卡肉 0.06s 冻结→自动恢复检验通过，全局 time_scale 恒 1.0")
		phase = "knockback"
		tick = 0

## ================= 阶段 F：顺切线受击推力刹停 + 高亮白闪 =================
func phase_knockback() -> void:
	if tick == 1:
		print("--- 顺切线受击推力 + Hit Flash 门禁 ---")
		var cd: CombatData = player.combat_data
		check(is_equal_approx(cd.knockback_light_distance, 0.35), "轻击推力距离应为 0.35m")
		check(cd.finisher_knock_distance >= 0.80 and cd.finisher_knock_distance <= 1.20, "4 段终结推力应落在 0.8~1.2m 重击档")
		check(is_equal_approx(cd.knockback_heavy_distance, 0.80), "居合默认重击推力应为 0.80m")
		check(is_equal_approx(cd.hit_flash_duration, 0.05), "受击白闪时长应为 0.05s")
		kb_dummy = scene.get_node_or_null("Zone1_Combat/TrainingDummy") as TrainingDummy
		check(kb_dummy != null, "TrainingDummy 未找到")
		if kb_dummy:
			# 轻击档：默认 0.35m 推移 + 0.05s 白闪当帧生效
			kb_dummy.reset_knockback()
			kb_dummy.take_hit(25.0, Vector3(1, 0, 0), false)
			check(kb_dummy.dummy_mat.albedo_color.r > 0.95 and kb_dummy.dummy_mat.albedo_color.g > 0.95
				and kb_dummy.dummy_mat.albedo_color.b > 0.95, "受击白闪未在当帧立即全亮")
	elif tick == 5 and kb_dummy:
		# 阻尼衰减特征：二次缓出在中点时刻已走完 75% 距离（先快后慢迅速刹停）
		var mid_offset: Vector3 = kb_dummy.mesh_root.position - kb_dummy.original_mesh_pos
		var mid_len: float = Vector2(mid_offset.x, mid_offset.z).length()
		check(mid_len > 0.35 * 0.6 and mid_len < 0.35 * 0.92,
			"轻击推力阻尼衰减特征异常（中点位移 %.3fm，应约 0.75 倍距离）" % mid_len)
	elif tick == 6 and kb_dummy:
		var c: Color = kb_dummy.dummy_mat.albedo_color
		var o: Color = kb_dummy._orig_albedo
		check(is_equal_approx(c.r, o.r) and is_equal_approx(c.g, o.g) and is_equal_approx(c.b, o.b),
			"0.05s 白闪结束后未恢复原材质")
		print("✔ 0.05s 纯材质高亮白闪：当帧全亮→线性消隐恢复")
	elif tick == 12 and kb_dummy:
		_kb_offset_light = kb_dummy.mesh_root.position - kb_dummy.original_mesh_pos
		var light_len: float = Vector2(_kb_offset_light.x, _kb_offset_light.z).length()
		check(absf(light_len - 0.35) < 0.04, "轻击推移终值应为 0.35m（实测 %.3fm）" % light_len)
		check(absf(_kb_offset_light.y) < 0.001, "木桩推移应贴地无垂直分量")
		print("✔ 轻击 0.35m 阶梯推力刹停检验通过")
	elif tick == 16 and kb_dummy:
		var settled: Vector3 = kb_dummy.mesh_root.position - kb_dummy.original_mesh_pos
		var drift: float = (settled - _kb_offset_light).length()
		check(drift < 0.005, "刹停后木桩仍在漂移（漂移 %.4fm）" % drift)
		# 4 段终结拔刀重击档：显式 1.0m 强力推力
		kb_dummy.reset_knockback()
		kb_dummy.take_hit(75.0, Vector3(1, 0, 0), true, 0.0, 1.0)
	elif tick == 32 and kb_dummy:
		var heavy_offset: Vector3 = kb_dummy.mesh_root.position - kb_dummy.original_mesh_pos
		var heavy_len: float = Vector2(heavy_offset.x, heavy_offset.z).length()
		check(absf(heavy_len - 1.0) < 0.05, "4 段终结重击推力应为 1.0m（实测 %.3fm）" % heavy_len)
		check(absf(heavy_offset.y) < 0.001, "重击推移同样保持贴地")
		print("✔ 重击 1.0m 强力推力检验通过（0.8~1.2m 档）")
		# 居合拔刀默认重击档
		kb_dummy.reset_knockback()
		kb_dummy.take_hit(110.0, Vector3(1, 0, 0), true)
	elif tick == 48 and kb_dummy:
		var iai_offset: Vector3 = kb_dummy.mesh_root.position - kb_dummy.original_mesh_pos
		var iai_len: float = Vector2(iai_offset.x, iai_offset.z).length()
		check(absf(iai_len - 0.80) < 0.05, "居合默认重击推力应为 0.80m（实测 %.3fm）" % iai_len)
		# 微弱刀锋切向分量：纯径向 -z 输入，终偏移方向应偏转 atan(0.15)≈8.5°
		kb_dummy.reset_knockback()
		kb_dummy.take_hit(25.0, Vector3(0, 0, -1), false)
	elif tick == 62 and kb_dummy:
		var tan_offset: Vector3 = kb_dummy.mesh_root.position - kb_dummy.original_mesh_pos
		var tan_len: float = Vector2(tan_offset.x, tan_offset.z).length()
		var radial_angle: float = rad_to_deg(atan2(absf(tan_offset.x), absf(tan_offset.z)))
		check(absf(tan_len - 0.35) < 0.04, "切向合成后推移距离仍应为 0.35m（实测 %.3fm）" % tan_len)
		check(radial_angle > 4.0 and radial_angle < 16.0,
			"受击方向未融入微弱切向分量（偏角 %.1f°，应约 8.5°）" % radial_angle)
		print("✔ 顺切线受击方向检验通过：径向 + 微弱刀锋切向分量")
		phase = "bullet_time"
		tick = 0

## ================= 阶段 G：极限闪避「星闪·时空断裂」 =================
func phase_bullet_time() -> void:
	if tick == 1:
		print("--- 星闪·时空断裂（Bullet Time）门禁 ---")
		var cd: CombatData = player.combat_data
		check(is_equal_approx(cd.time_dilation_factor, 0.20), "星闪局部减速倍率应为 0.20x")
		check(is_equal_approx(cd.time_dilation_duration, 0.50), "星闪局部减速应持续 0.50s")
		check(is_equal_approx(cd.bullet_time_fov_pulse, 4.0), "星闪 FOV 瞬冲应为 -4°")
		check(is_equal_approx(cd.bullet_time_fov_recover, 0.30), "星闪 FOV 回弹应为 0.30s")
		bt_drone = scene.get_node_or_null("Zone5_Drone/TrainingDrone") as TrainingDrone
		check(bt_drone != null, "TrainingDrone 未找到")
		if bt_drone:
			# 玩家传送到傀儡攻击范围内（侧方 2m，折跃轨迹与傀儡相切不阻挡）
			bt_drone.target_player = player
			player.velocity = Vector3.ZERO
			player.global_position = bt_drone.global_position + Vector3(2.0, 0.0, 0.5)
			fsm.change_state(PlayerCombatFSM.State.IDLE)
			bt_drone.start_telegraph()
			check(bt_drone.current_state == TrainingDrone.DroneState.TELEGRAPH, "傀儡未进入红光警示蓄力态")
	elif tick == 42 and bt_drone:
		# 蓄力 0.75s 尾声（命中判定前 0.12s 窗口内）起手极限闪避折跃
		fsm.change_state(PlayerCombatFSM.State.DASH)
		_dash_start_pos = player.global_position
	elif tick == 47 and bt_drone:
		# 傀儡 STRIKE 首帧命中结算：完美闪避窗口内 → 星闪时空断裂触发
		check(bt_drone.current_state == TrainingDrone.DroneState.STRIKE, "傀儡未进入突刺出招态")
		check(fsm.is_bullet_time_active, "星闪时空断裂标志位未置位")
		check(bt_drone.local_time_scale == player.combat_data.time_dilation_factor, "傀儡未减速至 0.2x")
		check(Engine.time_scale == 1.0, "星闪严禁降低全局 Engine.time_scale")
		check(is_equal_approx(player.hp, 100.0), "完美闪避未完全免伤")
		check(absf(player.velocity.length() - player.combat_data.dash_speed) < 1.0,
			"主角折跃应保持 1.0x 满速（实测 %.1f m/s）" % player.velocity.length())
		check(player.camera_controller.fov_pulse <= -3.0
			and player.camera_controller.camera.fov < player.camera_controller._fov_current,
			"星闪 FOV 未瞬冲收窄（脉冲 %.1f°，应 -4° 起回弹）" % player.camera_controller.fov_pulse)
		_drone_snap_timer = bt_drone.state_timer
		_drone_snap_pos = bt_drone.global_position
	elif tick == 48 and bt_drone:
		# 傀儡状态计时按 0.2x 推进（减速铁证 1）
		var timer_step: float = bt_drone.state_timer - _drone_snap_timer
		check(timer_step < 0.5 / 60.0, "傀儡状态计时未按 0.2x 减速（帧增量 %.4fs）" % timer_step)
		# 傀儡位移按 0.2x 推进（减速铁证 2：满速冲刺 16m/s 应达 0.267m/帧）
		var pos_step: float = bt_drone.global_position.distance_to(_drone_snap_pos)
		check(pos_step < 0.5 * 16.0 / 60.0, "傀儡位移未按 0.2x 减速（帧位移 %.3fm）" % pos_step)
		print("✔ 傀儡状态计时与位移双证据 0.2x 局部减速，主角与全局时间满速")
	elif tick == 52:
		# 折跃推进：DASH 10 帧应推进约 3.3m（全程 0.25s 共 5.0m）
		var dash_advance: Vector3 = player.global_position - _dash_start_pos
		dash_advance.y = 0.0
		check(dash_advance.length() > 2.9 and dash_advance.length() < 3.9,
			"折跃推进速度异常（10 帧推进 %.2fm，应约 3.3m）" % dash_advance.length())
	elif tick == 53:
		# 星闪触发后：折跃期间普攻缓冲立即取消（零前摇拔刀衔接）
		fsm.buffer_input("attack")
	elif tick == 54:
		check(fsm.current_state == PlayerCombatFSM.State.ATTACK, "星闪后零前摇拔刀取消未生效")
		print("✔ 折跃推进 + 星闪后零前摇拔刀立即取消检验通过")
	elif tick == 66:
		check(absf(player.camera_controller.fov_pulse) < 0.3,
			"星闪 FOV 脉冲 0.3s 回弹未完成（残留 %.2f°）" % player.camera_controller.fov_pulse)
		check(player.camera_controller.camera.fov > player.combat_data.fov_base,
			"星闪回弹后速度感 FOV 扩张被脉冲污染（当前 %.1f°）" % player.camera_controller.camera.fov)
		print("✔ 星闪运镜 FOV -4° 瞬冲→0.3s 平滑回弹检验通过")
	elif tick == 82 and bt_drone:
		check(bt_drone.local_time_scale == 1.0, "0.5s 局部减速结束后傀儡未恢复满速")
		check(not fsm.is_bullet_time_active, "星闪标志位 0.5s 后未自动复位")
		print("✔ 星闪 0.50s 局部时停自动恢复检验通过")
		phase = "weapon_mount"
		tick = 0

## ================= 阶段 H：武器挂载物理门禁（v5.2 三铁律） =================
func phase_weapon_mount() -> void:
	if tick != 1:
		return
	print("--- 武器挂载物理门禁（刀鞘口零偏置架构）---")
	# 复位纳刀态
	rig.sheathe_sword()
	check(rig.katana_blade.get_parent() == rig.scabbard_socket, "纳刀态刀身应挂左腰鞘插槽")
	# 断言1：物理抓握——拔刀态握心与掌心世界坐标物理距离 < 0.03m
	rig.draw_sword()
	var grip: Vector3 = rig.get_grip_center_world()
	var palm: Vector3 = rig.get_palm_center_world()
	var grip_dist := grip.distance_to(palm)
	check(grip_dist < 0.03, "刀柄握心与右手掌心物理距离应 < 0.03m（实测 %.4fm）" % grip_dist)
	check(rig.katana_blade.transform.origin.distance_to(AsterRig.DRAW_GRIP_COMPENSATION) < 0.001,
		"拔刀挂载位置应为 §3 握心补偿 (0,-0.13,0)（实测 %s）" % rig.katana_blade.transform.origin)
	print("  ✔ 物理抓握: 握心=%s 掌心=%s 距离=%.4fm" % [grip.snappedf(0.001), palm.snappedf(0.001), grip_dist])
	rig.sheathe_sword()
	# 断言2/3/4/5：插槽纯洁性 + Twist 洁净 + 长发锁头 + 零权重顶点（GLB 蒙皮数据真值）
	var res := _audit_skin_weights()
	check(res.socket_counts["Pelvis_L_Scabbard_Socket"] == 0,
		"Pelvis_L_Scabbard_Socket 顶点权重计数应恒为 0（实测 %d）" % res.socket_counts["Pelvis_L_Scabbard_Socket"])
	check(res.socket_counts["Hand_R_Weapon_Socket"] == 0,
		"Hand_R_Weapon_Socket 顶点权重计数应恒为 0（实测 %d）" % res.socket_counts["Hand_R_Weapon_Socket"])
	check(res.twist_weighted_verts == 0,
		"肢体 Twist 扭骨加权顶点数应恒为 0（实测 %d）" % res.twist_weighted_verts)
	check(res.hair_verts >= 500, "Hair_Mask 发丝标记顶点数应 ≥500（实测 %d）" % res.hair_verts)
	check(res.hair_bad_verts == 0,
		"发丝顶点在 Spine/Waist/Hip/腿骨上的权重应恒为 0（违例 %d 个）" % res.hair_bad_verts)
	check(res.zero_weight_verts == 0, "全网格零权重顶点数应为 0（实测 %d）" % res.zero_weight_verts)
	print("  ✔ 蒙皮审计: 加权顶点=%d Socket带权=%d/%d Twist带权=%d 发丝=%d(违例%d) 零权重=%d" % [
		res.weighted_verts, res.socket_counts["Pelvis_L_Scabbard_Socket"],
		res.socket_counts["Hand_R_Weapon_Socket"], res.twist_weighted_verts,
		res.hair_verts, res.hair_bad_verts, res.zero_weight_verts])
	phase = "done"


## 蒙皮权重审计：扫描 Aster_Body 全部表面权重数组 + Hair_Mask 顶点色
func _audit_skin_weights() -> Dictionary:
	var out := {
		"socket_counts": {"Pelvis_L_Scabbard_Socket": 0, "Hand_R_Weapon_Socket": 0},
		"zero_weight_verts": 0,
		"weighted_verts": 0,
		"twist_weighted_verts": 0,
		"hair_verts": 0,
		"hair_bad_verts": 0,
	}
	var mi := rig.skeleton.get_node_or_null("Aster_Body") as MeshInstance3D
	if mi == null or mi.mesh == null:
		_failures.append("Aster_Body 蒙皮网格缺失")
		return out
	# 扭骨集合（NeckTwist01 除外——它是保留形变的颈主骨）
	var twist_bones := {}
	for b in rig.skeleton.get_bone_count():
		var bn := rig.skeleton.get_bone_name(b)
		if bn.contains("Twist") and bn != "NeckTwist01":
			twist_bones[bn] = 0
	# 发丝锁头黑名单骨（发丝顶点在这些骨上的权重必须恒 0）
	var hair_forbidden := {"Spine01": 0, "Spine02": 0, "Waist": 0, "Hip": 0,
		"Pelvis": 0, "L_Thigh": 0, "R_Thigh": 0, "L_Calf": 0, "R_Calf": 0}
	var n_bones := rig.skeleton.get_bone_count()
	for s in mi.mesh.get_surface_count():
		var arrays := mi.mesh.surface_get_arrays(s)
		var bones := arrays[Mesh.ARRAY_BONES] as PackedInt32Array
		var weights := arrays[Mesh.ARRAY_WEIGHTS] as PackedFloat32Array
		if bones.is_empty() or weights.is_empty():
			continue
		# 发丝标记：Hair_UV 第二 UV 通道（发丝=(0.5,0.5)）→ glTF TEXCOORD_1
		var uv2: Variant = arrays[Mesh.ARRAY_TEX_UV2]
		var has_uv2: bool = uv2 is PackedVector2Array and uv2.size() >= weights.size() / 4
		var n := weights.size() / 4
		for i in n:
			var wsum := weights[i * 4] + weights[i * 4 + 1] + weights[i * 4 + 2] + weights[i * 4 + 3]
			if wsum < 0.0001:
				out.zero_weight_verts += 1
				continue
			out.weighted_verts += 1
			var is_hair: bool = has_uv2 and uv2[i].x > 0.25
			if is_hair:
				out.hair_verts += 1
			for k in 4:
				var bi := bones[i * 4 + k]
				var w := weights[i * 4 + k]
				if w <= 0.0001 or bi >= n_bones:
					continue
				var bn := rig.skeleton.get_bone_name(bi)
				if out.socket_counts.has(bn):
					out.socket_counts[bn] += 1
				if twist_bones.has(bn):
					out.twist_weighted_verts += 1
				if is_hair and hair_forbidden.has(bn):
					out.hair_bad_verts += 1
	return out
