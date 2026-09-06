extends SceneTree
## Ground physics alignment probe (第四执行组 Ground Pavement Pipeline).
## 无头诊断, 不随游戏发布:
##  1) 沿 x=0 走线 raycast 地面高度剖面, 验证 CS2_Collision_Hulls 从南侧广场
##     到中央坡道连续无缝 (不掉落空洞);
##  2) 胶囊体以 4 m/s 从广场南端跑到坡道北端, 验证爬坡不卡顿、不下坠穿模。

const WALK_LINE_X := 0.0
const PROFILE_Z_FROM := 34.0
const PROFILE_Z_TO := -24.0
const PROFILE_STEP := 1.0
const RUN_SPEED := 4.0
const SIM_FRAMES := 900          # 15s @60Hz, 足够跑完 ~58m 路程

var _body: CharacterBody3D
var _min_gap := 999.0
var _min_gap_info := ""
var _runner_ok := true


func _initialize() -> void:
	_run()


func _run() -> void:
	var ps: PackedScene = load("res://scenes/levels/modern_residential_sandbox.tscn")
	var scene := ps.instantiate()
	# 移除依赖 InputMap 的实体, 保证 -s 纯物理环境干净
	for n in ["Player", "TrainingDummy", "TrainingDrone"]:
		var c := scene.get_node_or_null(n)
		if c:
			c.free()
	root.add_child(scene)

	# --- 1) 碰撞高度剖面 ---
	for i in 10:
		await physics_frame
	var space := root.world_3d.direct_space_state
	var holes := 0
	var prev_y := -999.0
	var max_step := 0.0
	var profile := PackedStringArray()
	var z := PROFILE_Z_FROM
	while z >= PROFILE_Z_TO:
		var q := PhysicsRayQueryParameters3D.create(
				Vector3(WALK_LINE_X, 50.0, z), Vector3(WALK_LINE_X, -10.0, z))
		q.collision_mask = 1            # CS2_Collision_Hulls 所在层
		var hit := space.intersect_ray(q)
		if hit.is_empty():
			holes += 1
			profile.append("%.0f:HOLE" % z)
		else:
			var y: float = hit.position.y
			if prev_y > -998.0:
				max_step = maxf(max_step, absf(y - prev_y))
			prev_y = y
			profile.append("%.0f:%.2f" % [z, y])
		z -= PROFILE_STEP
	print("[probe] profile(z:y) = ", " ".join(profile))
	print("[probe] holes=%d max_step_per_m=%.3f" % [holes, max_step])

	# --- 2) 胶囊奔跑模拟 ---
	_body = CharacterBody3D.new()
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.3
	cap.height = 1.5
	cs.shape = cap
	_body.add_child(cs)
	_body.collision_mask = 1
	scene.add_child(_body)
	_body.global_position = Vector3(WALK_LINE_X, 0.8, 32.0)

	var reached := false
	for f in SIM_FRAMES:
		_body.velocity = Vector3(0.0, _body.velocity.y - 18.0 * 1.0 / 60.0, -RUN_SPEED)
		_body.move_and_slide()
		var p := _body.global_position
		if not is_finite(p.y) or p.y < -2.0:
			_runner_ok = false
			print("[probe] FAIL: runner fell through at frame=%d pos=%s" % [f, p])
			break
		# 贴地余量: 胶囊中心应始终高于地面射线 ~0.75±0.6
		var q2 := PhysicsRayQueryParameters3D.create(
				Vector3(p.x, p.y + 1.0, p.z), Vector3(p.x, p.y - 3.0, p.z))
		q2.collision_mask = 1
		q2.exclude = [_body.get_rid()]
		var h2 := space.intersect_ray(q2)
		if not h2.is_empty():
			var gap: float = p.y - 0.75 - h2.position.y
			if gap < _min_gap:
				_min_gap = gap
				_min_gap_info = "frame=%d pos=%.2f,%.2f,%.2f rayhit=%.2f" % [
						f, p.x, p.y, p.z, h2.position.y]
		if p.z <= -20.0 and p.y > 4.0:
			reached = true
			break
		await physics_frame

	print("[probe] runner end pos=%s reached_ramp_top=%s min_ground_gap=%.3f (%s)" % [
			_body.global_position, reached, _min_gap, _min_gap_info])
	var ok := holes == 0 and reached and _runner_ok and _min_gap > -0.35
	print("[probe] GROUND PHYSICS GATE: %s" % ("PASS" if ok else "FAIL"))
	quit(0 if ok else 1)
