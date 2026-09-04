extends SceneTree

var frame_count: int = 0
var scene: Node = null

func _initialize() -> void:
	print("--- 开始自动化战斗沙盒加载与完整性测试 ---")
	var scene_res: PackedScene = load("res://scenes/levels/combat_playground.tscn")
	if not scene_res:
		printerr("FAIL: 无法加载 combat_playground.tscn")
		quit(1)
		return
	scene = scene_res.instantiate()
	root.add_child(scene)

func _process(_delta: float) -> bool:
	frame_count += 1
	if frame_count == 4:
		# 检查 Player 实体
		var player: PlayerController = scene.get_node_or_null("Player") as PlayerController
		if not player:
			printerr("FAIL: 场景中未找到 PlayerController")
			quit(1)
			return true
		print("✔ PlayerController 存在且就绪")

		# 检查头部节点及材质
		var head: Node3D = player.visual_root.get_node_or_null("HeadPlaceholder")
		assert(head != null, "HeadPlaceholder 不存在")
		assert(head.has_node("HeadMesh"), "HeadMesh 不存在")
		print("✔ HeadPlaceholder 与 HeadMesh 配置完好")

		# 检查 CombatData 关键数值
		var cd: CombatData = player.combat_data
		assert(cd != null, "CombatData 为空")
		print("✔ CombatData 校验通过: walk=%.1f, sprint=%.1f, slide=%.1f, jump1=%.1f, jump2=%.1f, plunge=%.1f" % [
			cd.walk_speed, cd.sprint_speed, cd.slide_initial_speed, cd.jump_velocity_1, cd.jump_velocity_2, cd.plunge_speed
		])
		assert(cd.walk_speed == 4.5)
		assert(cd.sprint_speed == 7.0)
		assert(cd.slide_initial_speed == 12.0)
		assert(cd.slide_jump_momentum_keep == 0.90)
		assert(cd.plunge_speed == 24.0)
		assert(cd.max_wall_jumps == 3)
		assert(cd.perfect_dodge_window == 0.12)
		assert(cd.parry_window == 0.15)
		assert(cd.hitstop_heavy == 0.10)

		# 检查 HUD
		var hud: HUDController = scene.get_node_or_null("HUDLayer/HUD") as HUDController
		if not hud:
			printerr("FAIL: HUDLayer/HUD 未找到")
			quit(1)
			return true
		print("✔ HUDController 绑定就绪")

		# 检查靶子配置
		var dummies: Array = get_nodes_in_group("target_dummy")
		print("✔ 发现靶子数量: %d 个 (木桩与傀儡均在 target_dummy 分组)" % dummies.size())
		assert(dummies.size() >= 2, "靶子数量不足 2 个")

		# 检查 5 个特色地貌区域
		assert(scene.has_node("Zone1_Combat"), "缺少 Zone1_Combat")
		assert(scene.has_node("Zone2_Slope"), "缺少 Zone2_Slope")
		assert(scene.has_node("Zone3_Vertical"), "缺少 Zone3_Vertical")
		assert(scene.has_node("Zone4_WallBounce"), "缺少 Zone4_WallBounce")
		assert(scene.has_node("Zone5_Drone"), "缺少 Zone5_Drone")
		print("✔ 全部 5 大核心战斗与跑酷地貌检验通过")

		# 测试视角切换
		player.camera_controller.toggle_camera_mode()
		assert(player.camera_controller.current_mode == CameraController.CameraMode.FPP, "切换至 FPP 失败")
		assert(not head.visible, "第一人称下头部未隐藏")
		print("✔ FPP 视角切换及头部隐藏检验通过")

		player.camera_controller.toggle_camera_mode()
		assert(player.camera_controller.current_mode == CameraController.CameraMode.TPP, "切换回 TPP 失败")
		assert(head.visible, "第三人称下头部未重新显示")
		print("✔ TPP 视角恢复及头部显示检验通过")

		# 测试木桩受击机制
		var dummy: TrainingDummy = scene.get_node_or_null("Zone1_Combat/TrainingDummy") as TrainingDummy
		assert(dummy != null, "TrainingDummy 未找到")
		dummy.take_hit(25.0, Vector3.FORWARD, false)
		assert(dummy.hit_count == 1, "木桩受击计数未累加")
		assert(dummy.total_damage == 25.0, "木桩累计伤害未正确记录")
		print("✔ 木桩受击与飘字机制正常: hit_count=1, dmg=25")

		# 测试傀儡受击与破绽
		var drone: TrainingDrone = scene.get_node_or_null("Zone5_Drone/TrainingDrone") as TrainingDrone
		assert(drone != null, "TrainingDrone 未找到")
		drone.take_hit(50.0, Vector3.FORWARD, true)
		assert(drone.total_damage_taken == 50.0)
		print("✔ 傀儡受击机制正常: dmg=50")

		print("--- 全部自动化测试 100% 通过！---")
		quit(0)
		return true
	return false
