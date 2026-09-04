class_name HUDController
extends Control

## 战斗 HUD 控制器（身法状态、居合蓄力条、弹刀反馈与准星）

@onready var state_label: Label = $TopStatus/StateLabel
@onready var speed_label: Label = $TopStatus/SpeedLabel
@onready var view_mode_label: Label = $TopStatus/ViewModeLabel
@onready var charge_bar: ProgressBar = $CenterNotice/ChargeBar
@onready var feedback_notice: Label = $CenterNotice/FeedbackNotice
@onready var crosshair: Control = $Crosshair
@onready var crosshair_dot: ColorRect = $Crosshair/Dot
@onready var lock_bracket: Label = $Crosshair/LockBracket
@onready var hp_bar: ProgressBar = $BottomStatus/HPBar

var player: PlayerController = null
var notice_timer: float = 0.0

func _ready() -> void:
	charge_bar.visible = false
	feedback_notice.visible = false
	await get_tree().process_frame
	var players: Array = get_tree().get_nodes_in_group("player")
	if players.size() > 0:
		bind_player(players[0] as PlayerController)

func bind_player(p: PlayerController) -> void:
	player = p
	player.hp_changed.connect(_on_hp_changed)
	player.combat_fsm.state_changed.connect(_on_state_changed)
	player.combat_fsm.charge_tier_changed.connect(_on_charge_tier_changed)
	player.combat_fsm.perfect_parry_triggered.connect(_on_perfect_parry)
	player.combat_fsm.perfect_dodge_triggered.connect(_on_perfect_dodge)
	player.camera_controller.view_mode_changed.connect(_on_view_changed)

func _process(delta: float) -> void:
	if not player:
		return
		
	# 实时速度与状态显示
	var horiz_vel: float = Vector2(player.velocity.x, player.velocity.z).length()
	speed_label.text = "速度: %.1f m/s (水平)" % horiz_vel
	
	# 准星近战软吸附视觉反馈
	if player.combat_fsm and player.combat_fsm.soft_lock_target:
		if crosshair_dot:
			crosshair_dot.color = Color(0.2, 1.0, 0.85, 1.0)
		if lock_bracket:
			lock_bracket.add_theme_color_override("font_color", Color(0.2, 1.0, 0.85, 0.95))
			var pulse: float = 1.0 + sin(Time.get_ticks_msec() * 0.008) * 0.08
			lock_bracket.scale = Vector2(pulse, pulse)
			lock_bracket.pivot_offset = lock_bracket.size * 0.5
	else:
		if crosshair_dot:
			crosshair_dot.color = Color(1.0, 1.0, 1.0, 0.85)
		if lock_bracket:
			lock_bracket.add_theme_color_override("font_color", Color(0.2, 1.0, 0.85, 0.0))
			lock_bracket.scale = Vector2.ONE
	
	if notice_timer > 0.0:
		notice_timer -= delta
		if notice_timer <= 0.0:
			feedback_notice.visible = false

func _on_state_changed(_old: PlayerCombatFSM.State, new_st: PlayerCombatFSM.State) -> void:
	var state_name: String = ""
	match new_st:
		PlayerCombatFSM.State.IDLE: state_name = "待命 (IDLE)"
		PlayerCombatFSM.State.MOVE: state_name = "移动 (WALK)"
		PlayerCombatFSM.State.SPRINT: state_name = "疾跑 (SPRINT)"
		PlayerCombatFSM.State.SLIDE: state_name = "贴地滑铲 (SLIDE)"
		PlayerCombatFSM.State.JUMP_1: state_name = "一段跳 (JUMP 1)"
		PlayerCombatFSM.State.JUMP_2: state_name = "二段跳 (DOUBLE JUMP)"
		PlayerCombatFSM.State.WALL_JUMP: state_name = "蹬墙反弹 (WALL BOUNCE)"
		PlayerCombatFSM.State.PLUNGE: state_name = "星坠断空 (PLUNGE)"
		PlayerCombatFSM.State.DASH: state_name = "极闪突进 (DASH)"
		PlayerCombatFSM.State.ATTACK: state_name = "流光刀术 (COMBO %d)" % (player.combat_fsm.combo_index + 1)
		PlayerCombatFSM.State.GUARD_CHARGE: state_name = "纳刀架刀蓄力中..."
		PlayerCombatFSM.State.IAIJUTSU_DASH: state_name = "居合瞬步斩！"
		PlayerCombatFSM.State.PARRY_STUN: state_name = "完美弹刀！"
	state_label.text = "动作状态: %s" % state_name

func _on_charge_tier_changed(tier: int) -> void:
	if tier == 0:
		charge_bar.visible = false
	else:
		charge_bar.visible = true
		charge_bar.value = tier
		var tier_text: String = ""
		match tier:
			1: tier_text = "【居合 1 阶】轻拔刀横斩"
			2: tier_text = "【居合 2 阶】苍蓝星月斩"
			3: tier_text = "【居合 满阶】金芒次元穿透斩！"
		show_notice(tier_text, Color(1.0, 0.85, 0.2))

func _on_perfect_parry() -> void:
	show_notice("⚡ 完美弹刀 (PERFECT PARRY)! 敌人大破绽！", Color(1.0, 0.9, 0.1), 1.2)

func _on_perfect_dodge() -> void:
	show_notice("✨ 星闪极避 (PERFECT DODGE)! 全场减速时停！", Color(0.3, 0.9, 1.0), 1.2)

func _on_view_changed(is_fpp: bool) -> void:
	view_mode_label.text = "当前视角: %s (按 V 键切换)" % ("第一人称主观" if is_fpp else "第三人称越肩跟随")

func _on_hp_changed(cur: float, max_v: float) -> void:
	hp_bar.value = (cur / max_v) * 100.0

func show_notice(msg: String, col: Color = Color.WHITE, duration: float = 0.8) -> void:
	feedback_notice.text = msg
	feedback_notice.modulate = col
	feedback_notice.visible = true
	notice_timer = duration
