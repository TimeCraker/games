class_name PlayerController
extends CharacterBody3D

## Aster 角色物理与战斗主控制器（解耦型设计，支持无缝挂载未来 3D 模型）

@export var combat_data: CombatData

@onready var collision_shape: CollisionShape3D = $CollisionShape3D
@onready var visual_root: Node3D = $VisualRoot
@onready var camera_controller: CameraController = $CameraController
@onready var combat_fsm: PlayerCombatFSM = $PlayerCombatFSM
@onready var blade_hitbox: Area3D = $VisualRoot/BladeHitbox
@onready var blade_visual: MeshInstance3D = $VisualRoot/BladeVisual

var input_direction: Vector3 = Vector3.ZERO
var move_velocity: Vector3 = Vector3.ZERO
var slide_direction: Vector3 = Vector3.FORWARD
var current_max_speed: float = 4.5
var original_capsule_height: float = 1.8
var original_capsule_radius: float = 0.4

# 状态物理缓存
var is_sliding: bool = false
var is_sliding_attack: bool = false
var slide_speed: float = 0.0
var hp: float = 100.0
var max_hp: float = 100.0

# 蹬墙跳物理缓冲
var wall_contact_timer: float = 0.0
var cached_wall_normal: Vector3 = Vector3.ZERO

# 视觉表现与动效
var original_blade_transform: Transform3D
var blade_material: StandardMaterial3D
var attack_tween: Tween = null

signal hp_changed(current: float, max: float)
signal attack_hit_target(target: Node3D, damage: float, is_heavy: bool)

func _ready() -> void:
	if not combat_data:
		combat_data = CombatData.new()
	combat_fsm.init(self, combat_data)
	blade_hitbox.monitoring = false
	original_blade_transform = blade_visual.transform
	
	# 初始化独立佩刀材质 (支持运行时动态变光与阶数变色)
	blade_material = StandardMaterial3D.new()
	blade_material.albedo_color = Color(0.85, 0.95, 1.0)
	blade_material.emission_enabled = true
	blade_material.emission = Color(0.3, 0.7, 1.0)
	blade_material.emission_energy_multiplier = 2.0
	blade_visual.set_surface_override_material(0, blade_material)
	
	# 连接第一人称与蓄力阶数信号
	camera_controller.view_mode_changed.connect(_on_view_mode_changed)
	combat_fsm.charge_tier_changed.connect(_on_charge_tier_changed)

func _unhandled_input(event: InputEvent) -> void:
	combat_fsm.handle_input(event)

func _physics_process(delta: float) -> void:
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
	
	# 视觉根节点贴地俯冲姿态 (更强推背感)
	var tween: Tween = create_tween()
	tween.tween_property(visual_root, "position:y", -0.45, 0.08).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
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
	slide_direction = input_direction if input_direction.length_squared() > 0.01 else -visual_root.global_transform.basis.z

func start_guard_stance() -> void:
	# 纳刀架刀低姿态
	if attack_tween and attack_tween.is_valid():
		attack_tween.kill()
	attack_tween = create_tween()
	attack_tween.tween_property(blade_visual, "position", Vector3(-0.25, 0.75, 0.1), 0.12)
	attack_tween.parallel().tween_property(blade_visual, "rotation_degrees", Vector3(-20, 80, -75), 0.12)

func _on_charge_tier_changed(tier: int) -> void:
	if not blade_material:
		return
	match tier:
		0:
			blade_material.emission = Color(0.3, 0.7, 1.0)
			blade_material.emission_energy_multiplier = 2.0
		1: # 1阶：苍蓝微光
			blade_material.emission = Color(0.2, 0.6, 1.0)
			blade_material.emission_energy_multiplier = 4.0
		2: # 2阶：星霜光环
			blade_material.emission = Color(0.1, 0.95, 1.0)
			blade_material.emission_energy_multiplier = 6.5
		3: # 3阶：金芒次元裂隙
			blade_material.emission = Color(1.0, 0.85, 0.15)
			blade_material.emission_energy_multiplier = 10.0

func execute_attack_step(stage: int, soft_target: Node3D) -> void:
	var lunge_pwr: float = combat_data.combo_lunge_speed[stage]
	var lunge_dir: Vector3 = -visual_root.global_transform.basis.z

	# 软锁定吸附微滑步 (Soft-lock)
	if soft_target and is_instance_valid(soft_target):
		var to_target: Vector3 = soft_target.global_position - global_position
		to_target.y = 0.0
		lunge_dir = to_target.normalized()
		lunge_pwr = minf(lunge_pwr + combat_data.soft_lock_pull_speed, to_target.length() * 8.0)

	# 滑铲横扫出刀时保留滑铲动量与顺坡加速，站立普攻才施加微突进位移
	if not (is_sliding_attack and is_sliding):
		velocity.x = lunge_dir.x * lunge_pwr
		velocity.z = lunge_dir.z * lunge_pwr

	# 程序化刀光动效 (Procedural Blade Animation)
	if attack_tween and attack_tween.is_valid():
		attack_tween.kill()
	attack_tween = create_tween()

	match stage:
		0: # 1段挑击：自右下斜向上挑斩
			blade_visual.position = Vector3(0.5, 0.4, -0.1)
			blade_visual.rotation_degrees = Vector3(40, -30, -50)
			blade_material.emission = Color(0.4, 0.85, 1.0)
			blade_material.emission_energy_multiplier = 4.0
			attack_tween.tween_property(blade_visual, "position", Vector3(-0.2, 1.2, -0.6), 0.12).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
			attack_tween.parallel().tween_property(blade_visual, "rotation_degrees", Vector3(-60, 45, 50), 0.12)
			attack_tween.tween_property(blade_visual, "transform", original_blade_transform, 0.18).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
			attack_tween.parallel().tween_property(blade_material, "emission_energy_multiplier", 2.0, 0.18)
		1: # 2段反削：自左向右高速平削
			blade_visual.position = Vector3(-0.35, 1.0, -0.4)
			blade_visual.rotation_degrees = Vector3(-10, 60, 40)
			blade_material.emission = Color(0.3, 0.9, 1.0)
			blade_material.emission_energy_multiplier = 4.5
			attack_tween.tween_property(blade_visual, "position", Vector3(0.55, 0.8, -0.5), 0.12).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
			attack_tween.parallel().tween_property(blade_visual, "rotation_degrees", Vector3(10, -70, -40), 0.12)
			attack_tween.tween_property(blade_visual, "transform", original_blade_transform, 0.18).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
			attack_tween.parallel().tween_property(blade_material, "emission_energy_multiplier", 2.0, 0.18)
		2: # 3段双连刺：疾风双连刺
			blade_material.emission = Color(0.6, 0.8, 1.0)
			blade_material.emission_energy_multiplier = 5.0
			attack_tween.tween_property(blade_visual, "position", Vector3(0.2, 0.9, -0.95), 0.07).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
			attack_tween.parallel().tween_property(blade_visual, "rotation_degrees", Vector3(0, 0, 90), 0.07)
			attack_tween.tween_property(blade_visual, "position", Vector3(0.2, 0.9, -0.3), 0.05)
			attack_tween.tween_property(blade_visual, "position", Vector3(0.1, 0.9, -1.05), 0.07).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
			attack_tween.tween_property(blade_visual, "transform", original_blade_transform, 0.15)
			attack_tween.parallel().tween_property(blade_material, "emission_energy_multiplier", 2.0, 0.15)
		3: # 4段回旋气刃：360度周身回旋气刃斩
			blade_material.emission = Color(1.0, 0.8, 0.3)
			blade_material.emission_energy_multiplier = 7.0
			blade_visual.position = Vector3(0.6, 0.85, -0.3)
			blade_visual.rotation_degrees = Vector3(0, -90, 0)
			attack_tween.tween_property(visual_root, "rotation:y", visual_root.rotation.y + TAU, 0.22).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
			attack_tween.tween_property(blade_visual, "transform", original_blade_transform, 0.15)
			attack_tween.parallel().tween_property(blade_material, "emission_energy_multiplier", 2.0, 0.15)

	# 产生刀光弧刃与 Hitbox 判定
	spawn_slash_arc(stage)
	check_blade_hits(combat_data.combo_damage[stage], stage == 3)

func execute_iaijutsu(tier: int) -> void:
	if tier < 1:
		return
	var idx: int = tier - 1
	var dash_dist: float = combat_data.charge_dash_distances[idx]
	var dmg: float = combat_data.charge_damages[idx]
	var fwd: Vector3 = -visual_root.global_transform.basis.z

	# 极速瞬步穿透
	velocity = fwd * (dash_dist / 0.22)
	
	# 居合拔刀横斩
	if attack_tween and attack_tween.is_valid():
		attack_tween.kill()
	attack_tween = create_tween()
	blade_visual.position = Vector3(-0.4, 0.85, 0.1)
	blade_visual.rotation_degrees = Vector3(0, 90, 0)
	attack_tween.tween_property(blade_visual, "position", Vector3(0.6, 0.85, -0.6), 0.15).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
	attack_tween.parallel().tween_property(blade_visual, "rotation_degrees", Vector3(0, -90, 0), 0.15)
	attack_tween.tween_property(blade_visual, "transform", original_blade_transform, 0.12)

	# 判定路径上全部敌人并释放居合光芒
	spawn_slash_arc(3)
	check_blade_hits(dmg, true)

func check_blade_hits(damage: float, is_heavy: bool) -> void:
	# 沿刀刃挥击范围进行球形/扇形重叠检测
	var space_state: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	var query: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()
	var sphere: SphereShape3D = SphereShape3D.new()
	sphere.radius = 2.4
	query.shape = sphere
	query.transform = Transform3D(Basis(), global_position + -visual_root.global_transform.basis.z * 1.5 + Vector3.UP * 1.0)
	var hits: Array[Dictionary] = space_state.intersect_shape(query)
	
	var hit_count: int = 0
	for hit in hits:
		var collider: Object = hit.collider
		if collider.has_method("take_hit") and collider != self:
			collider.take_hit(damage, -visual_root.global_transform.basis.z, is_heavy)
			attack_hit_target.emit(collider, damage, is_heavy)
			spawn_hit_spark(collider.global_position + Vector3(0, 1.2, 0), is_heavy)
			hit_count += 1

	if hit_count > 0:
		# 触发卡肉顿帧与震屏
		camera_controller.trigger_hit_impact(is_heavy)

func play_parry_fx() -> void:
	camera_controller.trigger_hit_impact(true)
	spawn_hit_spark(blade_visual.global_position, true)
	if blade_material:
		blade_material.emission = Color(1.0, 0.9, 0.2)
		blade_material.emission_energy_multiplier = 10.0
		var mat_tween: Tween = create_tween()
		mat_tween.tween_property(blade_material, "emission_energy_multiplier", 2.0, 0.35)
		mat_tween.parallel().tween_property(blade_material, "emission", Color(0.3, 0.7, 1.0), 0.35)
	# 振刀火花与后仰震退反馈
	velocity = visual_root.global_transform.basis.z * 4.0
	var recoil_tween: Tween = create_tween()
	recoil_tween.tween_property(visual_root, "position:z", 0.25, 0.06)
	recoil_tween.tween_property(visual_root, "position:z", 0.0, 0.2).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)

func spawn_slash_arc(stage: int) -> void:
	var arc: MeshInstance3D = MeshInstance3D.new()
	var torus: TorusMesh = TorusMesh.new()
	torus.inner_radius = 1.0
	torus.outer_radius = 1.7
	arc.mesh = torus
	
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	
	match stage:
		0: mat.albedo_color = Color(0.35, 0.85, 1.0, 0.75)
		1: mat.albedo_color = Color(0.25, 0.95, 0.85, 0.8)
		2: mat.albedo_color = Color(0.65, 0.8, 1.0, 0.85)
		3: mat.albedo_color = Color(1.0, 0.85, 0.2, 0.9)
	
	arc.material_override = mat
	visual_root.add_child(arc)
	if camera_controller and camera_controller.current_mode == CameraController.CameraMode.FPP:
		arc.position = Vector3(0, 1.35, -0.65)
	else:
		arc.position = Vector3(0, 0.9, -0.6)
	
	match stage:
		0: arc.rotation_degrees = Vector3(35, 45, -20)
		1: arc.rotation_degrees = Vector3(0, 0, 15)
		2: arc.rotation_degrees = Vector3(90, 0, 0)
		3: arc.rotation_degrees = Vector3(0, 0, 0)
		
	var tween: Tween = arc.create_tween()
	tween.set_parallel(true)
	tween.tween_property(arc, "scale", Vector3(1.3, 1.3, 1.3), 0.16).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(mat, "albedo_color:a", 0.0, 0.16)
	tween.finished.connect(arc.queue_free)

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
	# 第一人称下隐藏自身头部以防穿模
	var head_node: Node3D = visual_root.get_node_or_null("HeadPlaceholder")
	if head_node:
		head_node.visible = not is_first_person
