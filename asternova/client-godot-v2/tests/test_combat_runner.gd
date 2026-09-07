extends SceneTree

## 自动化战斗门禁：场景完整性 + 动捕动画系统 + 移动混合 + 四段连招 + 拔刀联动 + 局部卡肉
## 运行： godot --headless --path client-godot-v2 -s tests/test_combat_runner.gd

var tick: int = 0
var scene: Node = null
var phase: String = "boot"
var player: PlayerController = null
var rig: AsterRig = null
var fsm: PlayerCombatFSM = null
var driver: AsterAnimDriver = null

# 连招测试状态
var combo_round: int = 0
var combo_seen: Array[int] = []
var _bone_pose_before: Quaternion = Quaternion.IDENTITY
var _failures: Array[String] = []

func check(cond: bool, msg: String) -> void:
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
	return false

func _maybe_quit() -> bool:
	if not _failures.is_empty():
		printerr("--- 门禁未通过：%d 项失败 ---" % _failures.size())
		quit(1)
		return true
	if phase == "done":
		print("--- 全部自动化测试 100% 通过！---")
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
	check(rig.skeleton != null and rig.skeleton.get_bone_count() == 43, "Aster 骨骼数量异常")
	check(rig.hand_socket != null and rig.hand_socket is BoneAttachment3D, "Hand_R_Weapon_Socket 插槽缺失")
	check(rig.scabbard_socket != null and rig.scabbard_socket is BoneAttachment3D, "Pelvis_L_Scabbard_Socket 插槽缺失")
	check(rig.katana_blade != null, "Katana_Blade 刀身网格缺失")
	print("✔ Aster 真身 rig 就绪: 43 骨骼 / 双插槽 / 刀身网格齐备")

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
		var now := rig.skeleton.get_bone_global_pose(idx).basis.get_rotation_quaternion()
		var ang := rad_to_deg(now.angle_to(_bone_pose_before))
		check(ang > 6.0, "骨骼姿态未被动捕数据驱动（R_Upperarm 变化仅 %.2f°）" % ang)
		print("✔ 动捕数据驱动验证: R_Upperarm 姿态变化 %.1f°（Slash1 蓄力段）" % ang)
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
		phase = "done"
