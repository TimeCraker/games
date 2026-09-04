class_name PlayerCombatFSM
extends Node

## 角色动作与战斗状态机（0.18s 输入缓冲 + 随时打断取消 + 软锁定索敌）

enum State {
	IDLE,
	MOVE,
	SPRINT,
	SLIDE,
	JUMP_1,
	JUMP_2,
	WALL_JUMP,
	FALL,
	PLUNGE,          ## 空中下砸
	DASH,            ## 极闪瞬步
	ATTACK,          ## 4段流光刀术
	GUARD_CHARGE,    ## 纳刀架刀蓄力
	IAIJUTSU_DASH,   ## 居合穿透拔刀
	PARRY_STUN       ## 完美弹刀振刀反馈
}

signal state_changed(old_state: State, new_state: State)
signal combo_stage_changed(stage: int)
signal charge_tier_changed(tier: int)
signal perfect_dodge_triggered()
signal perfect_parry_triggered()

@export var combat_data: CombatData

var current_state: State = State.IDLE
var player: CharacterBody3D

# 计时器与计数器
var state_time: float = 0.0
var combo_index: int = 0          # 0, 1, 2, 3 对应 4 段普攻
var combo_reset_timer: float = 0.0
var charge_timer: float = 0.0
var current_charge_tier: int = 0   # 0: 无, 1: 1阶, 2: 2阶, 3: 满阶
var dash_cooldown_timer: float = 0.0
var wall_jump_count: int = 0
var can_double_jump: bool = true
var input_buffer_action: String = ""
var input_buffer_timer: float = 0.0

# 标志位
var is_invulnerable: bool = false
var can_cancel_recovery: bool = false
var soft_lock_target: Node3D = null

func init(parent_player: CharacterBody3D, data: CombatData) -> void:
	player = parent_player
	combat_data = data

func handle_input(event: InputEvent) -> void:
	# 收集输入缓冲
	if event.is_action_pressed("attack"):
		buffer_input("attack")
	elif event.is_action_pressed("slide"):
		buffer_input("slide")
	elif event.is_action_pressed("jump"):
		buffer_input("jump")
	elif event.is_action_pressed("sprint"):
		buffer_input("sprint")
	elif event.is_action_pressed("guard_charge"):
		buffer_input("guard_charge")

func buffer_input(action: String) -> void:
	input_buffer_action = action
	input_buffer_timer = combat_data.input_buffer_time

func _physics_process(delta: float) -> void:
	state_time += delta
	
	# 维护输入缓冲倒计时
	if input_buffer_timer > 0.0:
		input_buffer_timer -= delta
		if input_buffer_timer <= 0.0:
			input_buffer_action = ""

	# 连招重置倒计时
	if combo_reset_timer > 0.0:
		combo_reset_timer -= delta
		if combo_reset_timer <= 0.0:
			combo_index = 0
			combo_stage_changed.emit(0)

	# 闪避冷却
	if dash_cooldown_timer > 0.0:
		dash_cooldown_timer -= delta

	# 持续探测准星前方软锁定目标
	find_soft_lock_target()

	# 状态特异性物理逻辑
	match current_state:
		State.IDLE, State.MOVE, State.SPRINT:
			check_locomotion_transitions()
		State.SLIDE:
			process_slide(delta)
		State.JUMP_1, State.JUMP_2, State.WALL_JUMP, State.FALL:
			process_airborne(delta)
		State.PLUNGE:
			process_plunge(delta)
		State.DASH:
			process_dash(delta)
		State.ATTACK:
			process_attack(delta)
		State.GUARD_CHARGE:
			process_guard_charge(delta)
		State.IAIJUTSU_DASH:
			process_iaijutsu(delta)
		State.PARRY_STUN:
			if state_time >= 0.35:
				change_state(State.IDLE)

func check_locomotion_transitions() -> void:
	# 消耗缓冲的闪避输入
	if consume_buffer("sprint") and dash_cooldown_timer <= 0.0:
		change_state(State.DASH)
		return

	# 消耗缓冲的架刀输入
	if Input.is_action_pressed("guard_charge"):
		change_state(State.GUARD_CHARGE)
		return

	# 消耗缓冲的普攻
	if consume_buffer("attack"):
		start_attack_combo()
		return

	# 消耗缓冲的滑铲 (需处于地面且有移动意图)
	if consume_buffer("slide") and player.is_on_floor():
		change_state(State.SLIDE)
		return

	# 消耗缓冲的起跳
	if consume_buffer("jump") and player.is_on_floor():
		change_state(State.JUMP_1)
		return

	# 地面走跑与下落判定
	if not player.is_on_floor():
		change_state(State.FALL)
		return

	var is_moving: bool = player.input_direction.length_squared() > 0.01
	if is_moving:
		if Input.is_action_pressed("sprint"):
			if current_state != State.SPRINT:
				change_state(State.SPRINT)
		else:
			if current_state != State.MOVE:
				change_state(State.MOVE)
	else:
		if current_state != State.IDLE:
			change_state(State.IDLE)

func process_slide(delta: float) -> void:
	# 滑铲中按跳跃 -> 滑铲跳 (保留 90% 惯性)
	if consume_buffer("jump"):
		player.preserve_slide_jump_momentum()
		change_state(State.JUMP_1)
		return

	# 滑铲中普攻 -> 滑铲横扫出刀 (上下半身解耦：保持高速滑铲位移并挥刀)
	if consume_buffer("attack"):
		player.is_sliding_attack = true
		start_attack_combo()
		return

	# 滑铲中闪避 -> 切断滑铲
	if consume_buffer("sprint") and dash_cooldown_timer <= 0.0:
		change_state(State.DASH)
		return

	# 滑铲时间结束或脱离地面
	if state_time >= combat_data.slide_duration:
		change_state(State.MOVE if player.input_direction.length_squared() > 0.01 else State.IDLE)
	elif not player.is_on_floor():
		change_state(State.FALL)

func process_airborne(delta: float) -> void:
	# 1. 优先判定贴墙跳 (蹬墙跳 Wall Bounce，支持 0.18s 贴墙容错缓冲与夹墙连续折返)
	if (player.is_on_wall() or player.wall_contact_timer > 0.0) and wall_jump_count < combat_data.max_wall_jumps:
		if consume_buffer("jump"):
			change_state(State.WALL_JUMP)
			return

	# 2. 判定空中二段跳 (Double Jump)
	if can_double_jump and (current_state == State.JUMP_1 or current_state == State.FALL or current_state == State.WALL_JUMP):
		if consume_buffer("jump"):
			can_double_jump = false
			change_state(State.JUMP_2)
			return

	# 3. 判定空中星坠断空 (Plunge Attack: 空中按下蹲 C/Ctrl 或普攻 LMB)
	if consume_buffer("slide") or consume_buffer("attack"):
		change_state(State.PLUNGE)
		return

	# 4. 蹬墙跳后顶峰平滑转为下落
	if current_state == State.WALL_JUMP and state_time > 0.25 and player.velocity.y < 0.0:
		change_state(State.FALL)
		return

	# 5. 起跳顶峰转下落
	if (current_state == State.JUMP_1 or current_state == State.JUMP_2) and player.velocity.y < 0.0:
		change_state(State.FALL)
		return

	# 6. 着陆清空计数
	if player.is_on_floor():
		wall_jump_count = 0
		can_double_jump = true
		change_state(State.IDLE)

func process_plunge(delta: float) -> void:
	# 下砸直到落地
	if player.is_on_floor():
		player.trigger_plunge_impact()
		change_state(State.IDLE)

func process_dash(delta: float) -> void:
	# 维护无敌帧
	is_invulnerable = state_time < combat_data.dash_iframe_duration
	
	# 闪避期间允许预输入连招或滑铲
	if state_time >= combat_data.dash_duration:
		is_invulnerable = false
		dash_cooldown_timer = combat_data.dash_cooldown
		if consume_buffer("attack"):
			start_attack_combo()
		elif consume_buffer("slide") and player.is_on_floor():
			change_state(State.SLIDE)
		else:
			change_state(State.IDLE if player.is_on_floor() else State.FALL)

func start_attack_combo() -> void:
	# 索敌与软锁定 (Soft-lock)
	find_soft_lock_target()
	change_state(State.ATTACK)
	combo_stage_changed.emit(combo_index + 1)
	player.execute_attack_step(combo_index, soft_lock_target)

func process_attack(delta: float) -> void:
	# 普攻后半段 (0.15s 后) 允许被滑铲/闪避/架刀/跳跃强行切断 (Cancel Window)
	if state_time > 0.15:
		can_cancel_recovery = true
		if consume_buffer("sprint") and dash_cooldown_timer <= 0.0:
			player.is_sliding_attack = false
			change_state(State.DASH)
			return
		if consume_buffer("slide") and player.is_on_floor():
			player.is_sliding_attack = false
			change_state(State.SLIDE)
			return
		if consume_buffer("guard_charge"):
			player.is_sliding_attack = false
			change_state(State.GUARD_CHARGE)
			return
		if consume_buffer("jump") and player.is_on_floor():
			player.is_sliding_attack = false
			change_state(State.JUMP_1)
			return

	# 衔接下一段连击 (输入缓冲)
	if state_time > 0.20 and consume_buffer("attack"):
		combo_index = (combo_index + 1) % combat_data.combo_damage.size()
		start_attack_combo()
		return

	# 整段攻击收刀结束
	var current_attack_anim_len: float = 0.40 if combo_index < 3 else 0.55
	if state_time >= current_attack_anim_len:
		player.is_sliding_attack = false
		combo_reset_timer = combat_data.combo_timeout
		change_state(State.IDLE if player.is_on_floor() else State.FALL)

func process_guard_charge(delta: float) -> void:
	charge_timer += delta
	
	# 分段蓄力门槛
	if charge_timer >= combat_data.charge_tier_3_time:
		if current_charge_tier != 3:
			current_charge_tier = 3
			charge_tier_changed.emit(3)
	elif charge_timer >= combat_data.charge_tier_2_time:
		if current_charge_tier != 2:
			current_charge_tier = 2
			charge_tier_changed.emit(2)
	elif charge_timer >= combat_data.charge_tier_1_time:
		if current_charge_tier != 1:
			current_charge_tier = 1
			charge_tier_changed.emit(1)

	# 松开右键 -> 居合拔刀出鞘！
	if not Input.is_action_pressed("guard_charge"):
		if current_charge_tier > 0:
			change_state(State.IAIJUTSU_DASH)
		else:
			change_state(State.IDLE)

func process_iaijutsu(delta: float) -> void:
	# 居合穿透冲刺
	if state_time >= 0.28:
		current_charge_tier = 0
		charge_tier_changed.emit(0)
		change_state(State.IDLE)

func change_state(new_state: State) -> void:
	var old_state: State = current_state
	current_state = new_state
	state_time = 0.0
	can_cancel_recovery = false
	
	# 离开旧状态回调
	exit_state(old_state)
	# 进入新状态回调
	enter_state(new_state)
	
	state_changed.emit(old_state, new_state)

func enter_state(state: State) -> void:
	match state:
		State.SLIDE:
			player.start_slide()
		State.JUMP_1:
			player.apply_jump(combat_data.jump_velocity_1)
		State.JUMP_2:
			can_double_jump = false
			player.apply_jump(combat_data.jump_velocity_2)
			player.spawn_jump_ring()
		State.WALL_JUMP:
			wall_jump_count += 1
			player.apply_wall_jump()
		State.PLUNGE:
			player.start_plunge()
		State.DASH:
			player.start_dash()
		State.GUARD_CHARGE:
			charge_timer = 0.0
			current_charge_tier = 0
			charge_tier_changed.emit(0)
			player.start_guard_stance()
		State.IAIJUTSU_DASH:
			player.execute_iaijutsu(current_charge_tier)
		State.PARRY_STUN:
			player.play_parry_fx()

func exit_state(state: State) -> void:
	match state:
		State.SLIDE:
			if not player.is_sliding_attack:
				player.end_slide()
		State.ATTACK:
			if player.is_sliding_attack:
				player.is_sliding_attack = false
				player.end_slide()
		State.DASH:
			is_invulnerable = false

func consume_buffer(action: String) -> bool:
	if input_buffer_action == action and input_buffer_timer > 0.0:
		input_buffer_action = ""
		input_buffer_timer = 0.0
		return true
	return false

## 检测来自敌人的攻击判定（用于完美弹刀与星闪结算）
func check_incoming_attack(attack_dir: Vector3, damage: float) -> bool:
	# 1. 检测极闪时停 (受击判定前 0.12s 处于闪避初段)
	if current_state == State.DASH and state_time <= combat_data.perfect_dodge_window:
		perfect_dodge_triggered.emit()
		trigger_time_dilation()
		return false # 完全免伤
		
	# 2. 检测闪避无敌帧
	if is_invulnerable:
		return false # 免疫伤害
		
	# 3. 检测架刀状态下的完美弹刀 (按右键前 0.15s)
	if current_state == State.GUARD_CHARGE:
		if charge_timer <= combat_data.parry_window:
			# 触发完美弹刀
			perfect_parry_triggered.emit()
			change_state(State.PARRY_STUN)
			return false # 弹刀免伤并破招
		else:
			# 普通防御，减免 70% 伤害
			player.take_damage(damage * 0.3)
			return true

	# 受到完整伤害
	player.take_damage(damage)
	return true

func trigger_time_dilation() -> void:
	Engine.time_scale = combat_data.time_dilation_factor
	get_tree().create_timer(combat_data.time_dilation_duration, true, false, true).timeout.connect(
		func(): Engine.time_scale = 1.0
	)

func find_soft_lock_target() -> void:
	soft_lock_target = null
	if not player or not player.camera_controller or not player.camera_controller.camera:
		return
	var camera_fwd: Vector3 = -player.camera_controller.camera.global_transform.basis.z
	camera_fwd.y = 0.0
	camera_fwd = camera_fwd.normalized()
	
	var enemies: Array = get_tree().get_nodes_in_group("target_dummy")
	var closest_dist: float = combat_data.soft_lock_distance
	for enemy in enemies:
		if not enemy is Node3D:
			continue
		var to_enemy: Vector3 = enemy.global_position - player.global_position
		to_enemy.y = 0.0
		var dist: float = to_enemy.length()
		if dist <= closest_dist:
			var dot: float = camera_fwd.dot(to_enemy.normalized())
			if dot > 0.45: # 前方约 60 度锥角范围
				closest_dist = dist
				soft_lock_target = enemy
