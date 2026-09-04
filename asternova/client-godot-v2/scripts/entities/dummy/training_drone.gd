class_name TrainingDrone
extends CharacterBody3D

## 主动红光攻击傀儡（专供测试 0.15s 完美弹刀与 0.12s 极限闪避时停）

enum DroneState {
	IDLE,
	TELEGRAPH,   ## 蓄力抬手红光警示 (0.75s)
	STRIKE,      ## 瞬间突刺出招 (0.2s)
	RECOVERY,    ## 后摇收招 (0.8s)
	PARRIED      ## 被完美弹刀大硬直 (1.5s)
}

@onready var state_label: Label3D = $StateLabel
@onready var indicator_light: OmniLight3D = $IndicatorLight
@onready var mesh_root: Node3D = $MeshRoot

var current_state: DroneState = DroneState.IDLE
var state_timer: float = 0.0
var target_player: PlayerController = null
var attack_cooldown: float = 3.5
var total_damage_taken: float = 0.0
var has_hit_player: bool = false

func _ready() -> void:
	add_to_group("target_dummy")
	indicator_light.light_color = Color(0.2, 0.7, 1.0) # 待机蓝光
	update_state_label("待机观察中...")

func _physics_process(delta: float) -> void:
	state_timer += delta
	
	if not target_player:
		var players: Array = get_tree().get_nodes_in_group("player")
		if players.size() > 0:
			target_player = players[0] as PlayerController

	match current_state:
		DroneState.IDLE:
			velocity = velocity.move_toward(Vector3.ZERO, 12.0 * delta)
			indicator_light.light_color = Color(0.2, 0.7, 1.0)
			if state_timer >= attack_cooldown and target_player:
				var dist: float = global_position.distance_to(target_player.global_position)
				if dist <= 14.0:
					start_telegraph()
		DroneState.TELEGRAPH:
			velocity = velocity.move_toward(Vector3.ZERO, 12.0 * delta)
			# 朝向玩家，红光高频闪烁警示 (0.75s 抬手)
			look_at_player(delta)
			var flash: float = sin(state_timer * 25.0) * 0.5 + 0.5
			indicator_light.light_color = Color(1.0, flash * 0.2, flash * 0.2)
			indicator_light.light_energy = 3.0 + flash * 5.0
			if state_timer >= 0.75:
				execute_strike()
		DroneState.STRIKE:
			if not has_hit_player and target_player:
				var dist: float = global_position.distance_to(target_player.global_position)
				if dist <= 3.2:
					has_hit_player = true
					var attack_dir: Vector3 = (target_player.global_position - global_position).normalized()
					var hit_success: bool = target_player.combat_fsm.check_incoming_attack(attack_dir, 35.0)
					if not hit_success:
						if target_player.combat_fsm.current_state == PlayerCombatFSM.State.PARRY_STUN:
							on_parried()
							return
			if state_timer >= 0.35:
				current_state = DroneState.RECOVERY
				state_timer = 0.0
				update_state_label("收招回退...")
		DroneState.RECOVERY:
			velocity = velocity.move_toward(Vector3.ZERO, 15.0 * delta)
			indicator_light.light_energy = 1.0
			indicator_light.light_color = Color(0.6, 0.6, 0.6)
			if state_timer >= 0.8:
				current_state = DroneState.IDLE
				state_timer = 0.0
				update_state_label("待机中...")
		DroneState.PARRIED:
			velocity = velocity.move_toward(Vector3.ZERO, 10.0 * delta)
			indicator_light.light_color = Color(1.0, 0.85, 0.1) # 金光破绽
			if state_timer >= 1.5:
				current_state = DroneState.IDLE
				state_timer = 0.0
				update_state_label("待机中...")

	move_and_slide()

func start_telegraph() -> void:
	current_state = DroneState.TELEGRAPH
	state_timer = 0.0
	has_hit_player = false
	update_state_label("⚠️ 蓄力攻击警示！准备弹刀/闪避！")

func execute_strike() -> void:
	current_state = DroneState.STRIKE
	state_timer = 0.0
	has_hit_player = false
	update_state_label("💥 突刺出刀！")

	if target_player:
		var attack_dir: Vector3 = (target_player.global_position - global_position).normalized()
		velocity = attack_dir * 16.0

func on_parried() -> void:
	current_state = DroneState.PARRIED
	state_timer = 0.0
	has_hit_player = true
	velocity = -transform.basis.z * 7.0 # 被震飞后仰
	update_state_label("⚡ PARRIED! 弹刀大破绽！受到伤害翻倍！")

func take_hit(damage: float, hit_dir: Vector3, is_heavy: bool) -> void:
	var final_damage: float = damage
	if current_state == DroneState.PARRIED:
		final_damage *= 2.0 # 破绽状态下双倍暴击伤害！
	
	total_damage_taken += final_damage
	var text_node: FloatingDamageText = FloatingDamageText.new()
	add_child(text_node)
	text_node.setup(final_damage, current_state == DroneState.PARRIED or is_heavy, global_position + Vector3(0, 2.0, 0))

	# 受击微后仰
	velocity += hit_dir * (6.0 if is_heavy else 3.0)

func look_at_player(delta: float) -> void:
	if not target_player:
		return
	var target_pos: Vector3 = target_player.global_position
	target_pos.y = global_position.y
	var target_transform: Transform3D = transform.looking_at(target_pos, Vector3.UP)
	transform.basis = transform.basis.slerp(target_transform.basis, delta * 10.0)

func update_state_label(msg: String) -> void:
	if state_label:
		state_label.text = "【红光陪练傀儡】\n%s" % msg
