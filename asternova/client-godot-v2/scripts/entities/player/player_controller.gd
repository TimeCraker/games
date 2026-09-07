class_name PlayerController
extends CharacterBody3D

## Aster 角色物理与战斗主控制器（解耦型设计，支持无缝挂载未来 3D 模型）

@export var combat_data: CombatData

@onready var collision_shape: CollisionShape3D = $CollisionShape3D
@onready var visual_root: Node3D = $VisualRoot
@onready var aster_rig: AsterRig = $VisualRoot/CharacterAster
@onready var camera_controller: CameraController = $CameraController
@onready var combat_fsm: PlayerCombatFSM = $PlayerCombatFSM

var input_direction: Vector3 = Vector3.ZERO
var move_velocity: Vector3 = Vector3.ZERO
var slide_direction: Vector3 = Vector3.FORWARD
var current_max_speed: float = 4.5
var original_capsule_height: float = 1.65
var original_capsule_radius: float = 0.38

# 状态物理缓存
var is_sliding: bool = false
var is_sliding_attack: bool = false
var slide_speed: float = 0.0
var hp: float = 100.0
var max_hp: float = 100.0

# 蹬墙跳物理缓冲
var wall_contact_timer: float = 0.0
var cached_wall_normal: Vector3 = Vector3.ZERO

# 磁性索敌吸附前突 (挥刀前摇窗口内的定向位移)
var attack_lunge_timer: float = 0.0
var attack_lunge_velocity: Vector3 = Vector3.ZERO

# 单体局部卡肉：命中瞬间冻结自身位姿与位移，倒计时后恢复（全局 time_scale 恒为 1.0）
var hitstop_timer: float = 0.0

signal hp_changed(current: float, max: float)
signal attack_hit_target(target: Node3D, damage: float, is_heavy: bool)

func _ready() -> void:
	if not combat_data:
		combat_data = CombatData.new()
	combat_fsm.init(self, combat_data)

	# AnimationTree 桥接驱动器：FSM 状态 → 动捕状态树 travel + Locomotion 混合参数
	var anim_driver := AsterAnimDriver.new()
	anim_driver.name = "AsterAnimDriver"
	add_child(anim_driver)
	anim_driver.init(combat_fsm, aster_rig, self)

	# 连接第一人称视角信号 (FPP 下隐藏真身防穿模)
	camera_controller.view_mode_changed.connect(_on_view_mode_changed)

func _unhandled_input(event: InputEvent) -> void:
	combat_fsm.handle_input(event)

func _physics_process(delta: float) -> void:
	# 单体局部卡肉：冻结期间暂停位移速度向量与位姿结算，摄像机与世界时间保持 1.0 满帧
	if hitstop_timer > 0.0:
		hitstop_timer -= delta
		velocity = Vector3.ZERO
		move_and_slide()
		return

	update_input_direction()
	
	# 状态机驱动不同运动模式
	match combat_fsm.current_state:
		PlayerCombatFSM.State.SLIDE:
			apply_slide_physics(delta)
		PlayerCombatFSM.State.DASH:
			apply_dash_physics(delta)
		PlayerCombatFSM.State.PLUNGE:
			apply_plunge_physics(delta)
		PlayerCombatFSM.State.ATTACK:
			apply_attack_physics(delta)
		PlayerCombatFSM.State.IAIJUTSU_DASH:
			apply_iaijutsu_physics(delta)
		PlayerCombatFSM.State.GUARD_CHARGE:
			apply_guard_physics(delta)
		_:
			apply_standard_movement(delta)

	# 执行 Godot 底层 C++ 物理移动与滑动
	move_and_slide()

	# 贴墙接触缓冲维护 (0.18s 容错窗口)
	if is_on_wall():
		wall_contact_timer = 0.18
		cached_wall_normal = get_wall_normal()
	elif wall_contact_timer > 0.0:
		wall_contact_timer -= delta

	# 通知运镜系统当前速度与状态 (驱动动态 FOV 与贴地俯冲)
	var horizontal_speed: float = Vector2(velocity.x, velocity.z).length()
	camera_controller.update_speed_feel(horizontal_speed, is_sliding, delta)

	# 朝向插值旋转
	align_visual_rotation(delta)

	# 虚空坠落保护（防从平台或滑道掉出世界）
	if global_position.y < -15.0:
		respawn()

func respawn() -> void:
	global_position = Vector3(0.0, 0.5, 4.0)
	velocity = Vector3.ZERO
	hp = max_hp
	hp_changed.emit(hp, max_hp)
	combat_fsm.change_state(PlayerCombatFSM.State.IDLE)
	camera_controller.add_trauma(0.1)

func update_input_direction() -> void:
	var raw_input: Vector2 = Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
	var cam_basis: Basis = camera_controller.camera.global_transform.basis
	var fwd: Vector3 = -cam_basis.z
	var right: Vector3 = cam_basis.x
	fwd.y = 0.0
	right.y = 0.0
	fwd = fwd.normalized()
	right = right.normalized()
	input_direction = (right * raw_input.x + fwd * -raw_input.y).normalized()

func apply_standard_movement(delta: float) -> void:
	# 确定目标地速
	if combat_fsm.current_state == PlayerCombatFSM.State.SPRINT:
		current_max_speed = combat_data.sprint_speed
	else:
		current_max_speed = combat_data.walk_speed

	# 重力解算 (下落时 1.8x 重力倍率，手感干脆不飘)
	if not is_on_floor():
		var grav: float = combat_data.base_gravity
		if velocity.y < 0.0:
			grav *= combat_data.fall_gravity_multiplier
		velocity.y -= grav * delta

	# 平面加速度与摩擦力解算
	var target_vel: Vector3 = input_direction * current_max_speed
	var accel: float = combat_data.acceleration if is_on_floor() else combat_data.acceleration * combat_data.air_control
	velocity.x = move_toward(velocity.x, target_vel.x, accel * delta)
	velocity.z = move_toward(velocity.z, target_vel.z, accel * delta)

func apply_slide_physics(delta: float) -> void:
	# 斜坡检测：下坡重力加速加成
	var floor_norm: Vector3 = get_floor_normal()
	var slope_angle: float = floor_norm.angle_to(Vector3.UP)
	var is_downhill: bool = false
	if is_on_floor() and slope_angle > deg_to_rad(4.0):
		# 判断滑行方向是否顺着斜坡向下
		var downhill_dir: Vector3 = (Vector3.DOWN - floor_norm * Vector3.DOWN.dot(floor_norm)).normalized()
		if slide_direction.dot(downhill_dir) > 0.2:
			is_downhill = true
			slide_speed += combat_data.slide_slope_acceleration * delta

	if not is_downhill:
		slide_speed = move_toward(slide_speed, 0.0, combat_data.slide_friction * delta)

	# 将滑行速度投影在地面斜坡切平面上，紧贴坡面防止颠簸脱地
	var move_dir: Vector3 = slide_direction
	if is_on_floor() and floor_norm.length_squared() > 0.01:
		move_dir = (slide_direction - floor_norm * slide_direction.dot(floor_norm)).normalized()
		floor_snap_length = 0.5
	else:
		floor_snap_length = 0.0

	velocity = move_dir * slide_speed
	if not is_on_floor():
		velocity.y -= combat_data.base_gravity * delta

func apply_dash_physics(delta: float) -> void:
	velocity.x = slide_direction.x * combat_data.dash_speed
	velocity.z = slide_direction.z * combat_data.dash_speed
	velocity.y = 0.0

func apply_plunge_physics(delta: float) -> void:
	velocity.x = move_toward(velocity.x, 0.0, 15.0 * delta)
	velocity.z = move_toward(velocity.z, 0.0, 15.0 * delta)
	velocity.y = -combat_data.plunge_speed

func apply_attack_physics(delta: float) -> void:
	if is_sliding_attack and is_sliding:
		# 滑铲中横扫出刀：上下半身解耦，保持贴地滑铲物理与斜坡重力加速
		apply_slide_physics(delta)
	else:
		# 磁性吸附前突窗口：匀速位移精准补偿 0.4m 距离，窗口结束即刻刹车防止惯性超程
		if attack_lunge_timer > 0.0:
			attack_lunge_timer -= delta
			velocity.x = attack_lunge_velocity.x
			velocity.z = attack_lunge_velocity.z
			if attack_lunge_timer <= 0.0:
				velocity.x = 0.0
				velocity.z = 0.0
		else:
			velocity.x = move_toward(velocity.x, 0.0, combat_data.friction * delta)
			velocity.z = move_toward(velocity.z, 0.0, combat_data.friction * delta)
		if not is_on_floor():
			velocity.y -= combat_data.base_gravity * delta

func apply_iaijutsu_physics(delta: float) -> void:
	# 居合极速穿透
	velocity.y = 0.0

func apply_guard_physics(delta: float) -> void:
	# 架刀时微步挪动
	var target_vel: Vector3 = input_direction * (combat_data.walk_speed * 0.35)
	velocity.x = move_toward(velocity.x, target_vel.x, combat_data.acceleration * delta)
	velocity.z = move_toward(velocity.z, target_vel.z, combat_data.acceleration * delta)
	if not is_on_floor():
		velocity.y -= combat_data.base_gravity * delta

func align_visual_rotation(delta: float) -> void:
	var look_dir: Vector3 = Vector3.ZERO
	if combat_fsm.current_state == PlayerCombatFSM.State.SLIDE or combat_fsm.current_state == PlayerCombatFSM.State.DASH:
		look_dir = slide_direction
	elif combat_fsm.current_state == PlayerCombatFSM.State.ATTACK:
		if combat_fsm.soft_lock_target and is_instance_valid(combat_fsm.soft_lock_target):
			look_dir = (combat_fsm.soft_lock_target.global_position - global_position).normalized()
			look_dir.y = 0.0
		elif input_direction.length_squared() > 0.01:
			look_dir = input_direction
	elif input_direction.length_squared() > 0.01:
		look_dir = input_direction

	if look_dir.length_squared() > 0.01:
		var target_y: float = atan2(-look_dir.x, -look_dir.z)
		visual_root.rotation.y = lerp_angle(visual_root.rotation.y, target_y, delta * 15.0)

# ==================== 身法与动作指令 ====================

func start_slide() -> void:
	is_sliding = true
	slide_direction = input_direction if input_direction.length_squared() > 0.01 else -visual_root.global_transform.basis.z
	slide_speed = combat_data.slide_initial_speed
	# 压低胶囊体碰撞高度与贴地吸附
	set_capsule_height(combat_data.slide_height)
	floor_snap_length = 0.5
	
	# 视觉根节点贴地俯冲姿态 (真身模型只做轻微下潜+前倾，避免腿部入地)
	var tween: Tween = create_tween()
	tween.tween_property(visual_root, "position:y", -0.12, 0.08).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(visual_root, "rotation:x", deg_to_rad(-12.0), 0.08)

func end_slide() -> void:
	is_sliding = false
	set_capsule_height(original_capsule_height)
	floor_snap_length = 0.1
	
	var tween: Tween = create_tween()
	tween.tween_property(visual_root, "position:y", 0.0, 0.12).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(visual_root, "rotation:x", 0.0, 0.12)

func preserve_slide_jump_momentum() -> void:
	# 滑铲跳保留 90% 前冲动量
	floor_snap_length = 0.0
	velocity.x = slide_direction.x * (slide_speed * combat_data.slide_jump_momentum_keep)
	velocity.z = slide_direction.z * (slide_speed * combat_data.slide_jump_momentum_keep)
	end_slide()

func apply_jump(jump_vel: float) -> void:
	floor_snap_length = 0.0
	velocity.y = jump_vel

func apply_wall_jump() -> void:
	var wall_norm: Vector3 = cached_wall_normal if cached_wall_normal.length_squared() > 0.01 else get_wall_normal()
	var bounce_dir: Vector3 = (wall_norm + Vector3.UP * 0.8).normalized()
	floor_snap_length = 0.0
	velocity = bounce_dir * combat_data.wall_jump_out_speed
	velocity.y = combat_data.wall_jump_up_speed
	slide_direction = wall_norm
	wall_contact_timer = 0.0
	# 触发蹬墙微镜头晃动与脚底反冲光环
	camera_controller.add_trauma(0.2)
	spawn_jump_ring()

func start_plunge() -> void:
	velocity.y = -5.0

func trigger_plunge_impact() -> void:
	camera_controller.trigger_hit_impact(true)
	# 产生环形冲击波视觉表现
	spawn_shockwave(combat_data.plunge_impact_radius)

	# 产生环形冲击波判定
	var space_state: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	var query: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()
	var sphere: SphereShape3D = SphereShape3D.new()
	sphere.radius = combat_data.plunge_impact_radius
	query.shape = sphere
	query.transform = global_transform
	var results: Array[Dictionary] = space_state.intersect_shape(query)
	for res in results:
		var collider: Object = res.collider
		if collider.has_method("take_hit") and collider != self:
			var knock_dir: Vector3 = (collider.global_position - global_position).normalized()
			knock_dir.y = 0.3
			collider.take_hit(80.0, knock_dir.normalized(), true)

func start_dash() -> void:
	# 星闪折跃方向优先级：鼠标准星水平朝向 > 移动输入 > 视觉前向（0.25s 高速破空推进 5.0m）
	var aim_dir: Vector3 = -camera_controller.camera.global_transform.basis.z
	aim_dir.y = 0.0
	if aim_dir.length_squared() > 0.01:
		slide_direction = aim_dir.normalized()
	elif input_direction.length_squared() > 0.01:
		slide_direction = input_direction
	else:
		slide_direction = -visual_root.global_transform.basis.z
	# 折跃前倾破空姿态（高速滑步的倾斜推进感）
	var lean_tween: Tween = create_tween()
	lean_tween.tween_property(visual_root, "rotation:x", deg_to_rad(-10.0), 0.06).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	lean_tween.tween_property(visual_root, "rotation:x", 0.0, 0.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)

func start_guard_stance() -> void:
	# 居合蓄力姿态由动捕状态树 IaiCharge（Guarding 循环剪辑）驱动，无需代码摆姿势
	pass

func update_blade_stance(drawn: bool) -> void:
	## 拔刀/纳刀插槽切换：由战斗状态机在状态迁移时驱动
	if drawn:
		aster_rig.draw_sword()
	else:
		aster_rig.sheathe_sword()

func begin_attack_lunge(lunge_dir: Vector3, distance: float, windup: float) -> void:
	## 磁性索敌吸附：前摇窗口内向目标匀速前突指定距离
	attack_lunge_timer = windup
	attack_lunge_velocity = lunge_dir * (distance / maxf(windup, 0.01))

func freeze_pose(duration: float) -> void:
	## 单体局部卡肉：仅冻结自身 AnimationTree 播放与位移，Engine.time_scale 恒 1.0
	hitstop_timer = maxf(hitstop_timer, duration)
	aster_rig.freeze_pose(duration)

func _trigger_screen_flash(duration: float) -> void:
	## 全屏闪白（居合穿透斩）：交由 HUD 层执行
	for hud in get_tree().get_nodes_in_group("hud"):
		if hud.has_method("flash_white"):
			hud.flash_white(duration)

func execute_attack_step(stage: int, soft_target: Node3D) -> void:
	# 出刀瞬间：刀身切换至右手掌心插槽
	update_blade_stance(true)

	# 磁性索敌吸附 (Soft-lock)：目标位于角色前方扇形内时，前摇窗口平滑前突补偿距离
	var lunge_dir: Vector3 = -visual_root.global_transform.basis.z
	var has_magnetic_target: bool = false
	var cone_dot: float = -1.0
	var pull: float = 0.0
	if soft_target and is_instance_valid(soft_target):
		var to_target: Vector3 = soft_target.global_position - global_position
		to_target.y = 0.0
		var dist: float = to_target.length()
		if dist > 0.01:
			var target_dir: Vector3 = to_target.normalized()
			var facing: Vector3 = -visual_root.global_transform.basis.z
			cone_dot = facing.normalized().dot(target_dir)
			if cone_dot >= cos(deg_to_rad(combat_data.magnetic_lunge_cone_deg)):
				lunge_dir = target_dir
				has_magnetic_target = true

	# 滑铲横扫出刀时保留滑铲动量与顺坡加速，站立普攻才施加吸附前突位移
	if has_magnetic_target and not (is_sliding_attack and is_sliding):
		var pull_to_target: Vector3 = soft_target.global_position - global_position
		pull_to_target.y = 0.0
		pull = minf(combat_data.magnetic_lunge_distance,
				maxf(pull_to_target.length() - combat_data.magnetic_lunge_stop_margin, 0.0))
		if pull > 0.01:
			begin_attack_lunge(lunge_dir, pull, combat_data.magnetic_lunge_windup)

	# Hitbox 判定对齐动捕节拍：挥砍中段（剪辑 35% 处）落刀判定
	var clip_len: float = maxf(combat_data.combo_anim_lengths[stage], 0.3)
	get_tree().create_timer(clip_len * 0.35).timeout.connect(func() -> void:
		check_blade_hits(stage)
	)

func execute_iaijutsu(tier: int) -> void:
	if tier < 1:
		return
	var idx: int = tier - 1
	var dash_dist: float = combat_data.charge_dash_distances[idx]
	var dmg: float = combat_data.charge_damages[idx]
	var fwd: Vector3 = -visual_root.global_transform.basis.z

	# 极速瞬步穿透
	velocity = fwd * (dash_dist / 0.22)

	# 居合拔刀横斩（出刀瞬间切换右手插槽 + 全屏闪白；判定对齐动捕节拍）
	update_blade_stance(true)
	_trigger_screen_flash(combat_data.iai_flash_duration)

	var release_len: float = maxf(combat_data.iai_release_length, 0.3)
	get_tree().create_timer(release_len * 0.30).timeout.connect(func() -> void:
		check_blade_hits_iai()
	)

func check_blade_hits(stage: int) -> void:
	## 沿刀刃挥击范围做球形重叠检测，并按段位施加分级单体卡肉与震屏
	var damage: float = combat_data.combo_damage[stage]
	var freeze: float = combat_data.hitstop_stage_freeze[stage]
	var trauma: float = combat_data.hit_trauma_stage[stage]
	# 阶梯推力：前 3 段轻击 0.35m，4 段终结拔刀强力推力 0.8~1.2m
	var knock: float = combat_data.finisher_knock_distance if stage == 3 else combat_data.knockback_light_distance
	var hit_colliders: Array = _query_blade_hits(damage, -visual_root.global_transform.basis.z, stage == 3, freeze, knock)

	if not hit_colliders.is_empty():
		camera_controller.add_trauma(trauma)
		freeze_pose(freeze)
		if stage == 2:
			# 3段双穿刺：0.03s + 0.06s 双段微卡肉
			var second_freeze: float = combat_data.hitstop_stage2_second
			get_tree().create_timer(combat_data.hitstop_stage2_gap).timeout.connect(func() -> void:
				freeze_pose(second_freeze)
				for collider in hit_colliders:
					if is_instance_valid(collider) and collider.has_method("apply_freeze"):
						collider.apply_freeze(second_freeze)
			)

func check_blade_hits_iai() -> void:
	## 居合穿透斩：路径上全部敌人，重卡肉 0.15s + 重击档强力推力
	var dmg: float = combat_data.charge_damages[combat_data.charge_damages.size() - 1]
	var hit_colliders: Array = _query_blade_hits(dmg, -visual_root.global_transform.basis.z, true, combat_data.hitstop_iaijutsu, combat_data.knockback_heavy_distance)
	if not hit_colliders.is_empty():
		camera_controller.add_trauma(combat_data.hit_trauma_iaijutsu)
		freeze_pose(combat_data.hitstop_iaijutsu)

func _query_blade_hits(damage: float, hit_dir: Vector3, is_heavy: bool, freeze: float, knock: float) -> Array:
	## 球形重叠检测并结算伤害/单体冻结/击退，返回受击者列表
	var space_state: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	var query: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()
	var sphere: SphereShape3D = SphereShape3D.new()
	sphere.radius = 2.4
	query.shape = sphere
	query.transform = Transform3D(Basis(), global_position + -visual_root.global_transform.basis.z * 1.5 + Vector3.UP * 1.0)
	var hits: Array[Dictionary] = space_state.intersect_shape(query)

	var hit_colliders: Array = []
	for hit in hits:
		var collider: Object = hit.collider
		if collider.has_method("take_hit") and collider != self:
			# 顺切线受击推力：径向 = 攻击者→受击者（受击方再叠加微弱刀锋切向分量）
			var radial: Vector3 = collider.global_position - global_position
			radial.y = 0.0
			if radial.length_squared() < 0.01:
				radial = hit_dir
			collider.take_hit(damage, radial.normalized(), is_heavy, freeze, knock)
			attack_hit_target.emit(collider, damage, is_heavy)
			spawn_hit_spark(collider.global_position + Vector3(0, 1.2, 0), is_heavy)
			hit_colliders.append(collider)
	return hit_colliders

func play_parry_fx() -> void:
	camera_controller.trigger_hit_impact(true)
	spawn_hit_spark(aster_rig.get_katana_position(), true)
	# 振刀火花与后仰震退反馈
	velocity = visual_root.global_transform.basis.z * 4.0
	var recoil_tween: Tween = create_tween()
	recoil_tween.tween_property(visual_root, "position:z", 0.25, 0.06)
	recoil_tween.tween_property(visual_root, "position:z", 0.0, 0.2).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)

func spawn_hit_spark(hit_pos: Vector3, is_heavy: bool) -> void:
	var spark: Node3D = Node3D.new()
	var mesh_inst: MeshInstance3D = MeshInstance3D.new()
	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(1.2, 0.22) if is_heavy else Vector2(0.65, 0.14)
	mesh_inst.mesh = quad
	
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(1.0, 0.9, 0.2, 1.0) if is_heavy else Color(0.4, 0.85, 1.0, 1.0)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mesh_inst.material_override = mat
	
	spark.add_child(mesh_inst)
	get_parent().add_child(spark)
	spark.global_position = hit_pos
	spark.rotation.z = randf_range(-PI, PI)
	
	var tween: Tween = spark.create_tween()
	tween.set_parallel(true)
	tween.tween_property(mesh_inst, "scale", Vector3(1.6, 0.1, 1.0), 0.15).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
	tween.tween_property(mat, "albedo_color:a", 0.0, 0.15)
	tween.finished.connect(spark.queue_free)

func spawn_shockwave(max_radius: float) -> void:
	var ring: MeshInstance3D = MeshInstance3D.new()
	var torus: TorusMesh = TorusMesh.new()
	torus.inner_radius = 0.2
	torus.outer_radius = 0.5
	ring.mesh = torus
	
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(0.3, 0.85, 1.0, 0.85)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	ring.material_override = mat
	
	get_parent().add_child(ring)
	ring.global_position = global_position + Vector3(0, 0.08, 0)
	
	var tween: Tween = ring.create_tween()
	tween.set_parallel(true)
	tween.tween_property(torus, "outer_radius", max_radius, 0.35).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(torus, "inner_radius", max_radius * 0.85, 0.35).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(mat, "albedo_color:a", 0.0, 0.35)
	tween.finished.connect(ring.queue_free)

func spawn_jump_ring() -> void:
	var ring: MeshInstance3D = MeshInstance3D.new()
	var torus: TorusMesh = TorusMesh.new()
	torus.inner_radius = 0.3
	torus.outer_radius = 0.5
	ring.mesh = torus
	
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(0.5, 0.9, 1.0, 0.9)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	ring.material_override = mat
	
	get_parent().add_child(ring)
	ring.global_position = global_position + Vector3(0, 0.1, 0)
	
	var tween: Tween = ring.create_tween()
	tween.set_parallel(true)
	tween.tween_property(torus, "outer_radius", 1.8, 0.25).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(torus, "inner_radius", 1.5, 0.25).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(mat, "albedo_color:a", 0.0, 0.25)
	tween.finished.connect(ring.queue_free)

func take_damage(amount: float) -> void:
	hp = maxf(0.0, hp - amount)
	hp_changed.emit(hp, max_hp)
	camera_controller.add_trauma(0.5)

func set_capsule_height(h: float) -> void:
	if collision_shape and collision_shape.shape is CapsuleShape3D:
		var capsule: CapsuleShape3D = collision_shape.shape as CapsuleShape3D
		capsule.height = h
		collision_shape.position.y = h * 0.5

func _on_view_mode_changed(is_first_person: bool) -> void:
	# 第一人称下隐藏整个真身模型以防穿模
	aster_rig.visible = not is_first_person
