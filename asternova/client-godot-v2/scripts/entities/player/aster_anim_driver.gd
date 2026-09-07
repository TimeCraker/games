class_name AsterAnimDriver
extends Node

## 战斗状态机 ↔ AnimationTree 桥接驱动器：
## - FSM 状态变化 → 状态树 travel（动捕剪辑间 0.15~0.2s CrossFade 由状态树资源定义）
## - 连招段位 → Combo1..4 状态
## - 每物理帧以实际水平速度驱动 Locomotion BlendSpace1D（引擎四元数 Slerp 插值踩地）
## 代码层零手搓骨骼姿态，仅负责状态路由与混合参数。

const STATE_TO_NODE := {
	PlayerCombatFSM.State.IDLE: "Locomotion",
	PlayerCombatFSM.State.MOVE: "Locomotion",
	PlayerCombatFSM.State.SPRINT: "Locomotion",
	PlayerCombatFSM.State.SLIDE: "Slide",
	PlayerCombatFSM.State.JUMP_1: "Jump",
	PlayerCombatFSM.State.JUMP_2: "Jump",
	PlayerCombatFSM.State.WALL_JUMP: "Jump",
	PlayerCombatFSM.State.FALL: "Fall",
	PlayerCombatFSM.State.PLUNGE: "Plunge",
	PlayerCombatFSM.State.DASH: "Dodge",
	PlayerCombatFSM.State.GUARD_CHARGE: "IaiCharge",
	PlayerCombatFSM.State.IAIJUTSU_DASH: "IaiSlash",
	PlayerCombatFSM.State.PARRY_STUN: "Parry",
}

var fsm: PlayerCombatFSM = null
var rig: AsterRig = null
var player: CharacterBody3D = null

## 供测试门禁与特效联动的只读计数
var combo_stage_fired: int = 0
var land_travel_count: int = 0

func init(f: PlayerCombatFSM, r: AsterRig, p: CharacterBody3D) -> void:
	fsm = f
	rig = r
	player = p
	fsm.state_changed.connect(_on_state_changed)
	fsm.combo_stage_changed.connect(_on_combo_stage)

func _on_state_changed(old_state: int, new_state: int) -> void:
	# 刀光条带：挥砍与居合态激活采样，其余状态自然淡出
	rig.set_trail_active(new_state in [
		PlayerCombatFSM.State.ATTACK, PlayerCombatFSM.State.IAIJUTSU_DASH])

	# ATTACK 由 combo_stage_changed 驱动 Combo1..4，不在此路由
	if new_state == PlayerCombatFSM.State.ATTACK:
		return

	# 空中态落地 → 先插着陆缓冲剪辑，AT_END 自动回归 Locomotion
	var was_airborne: bool = old_state in [
		PlayerCombatFSM.State.JUMP_1, PlayerCombatFSM.State.JUMP_2,
		PlayerCombatFSM.State.WALL_JUMP, PlayerCombatFSM.State.FALL,
		PlayerCombatFSM.State.PLUNGE]
	if was_airborne and new_state in [
			PlayerCombatFSM.State.IDLE, PlayerCombatFSM.State.MOVE,
			PlayerCombatFSM.State.SPRINT]:
		land_travel_count += 1
		rig.travel("Land")
		return

	rig.travel(STATE_TO_NODE.get(new_state, "Locomotion"))

func _on_combo_stage(stage: int) -> void:
	if stage > 0:
		combo_stage_fired = stage
		rig.travel("Combo%d" % stage)

func _physics_process(_delta: float) -> void:
	if rig == null or rig.anim_tree == null or player == null:
		return
	# 仅在 Locomotion 内持续驱动混合参数（0→idle, 2.8→walk, 7→run）
	if rig.get_current_state_node() == "Locomotion":
		var hspeed := Vector2(player.velocity.x, player.velocity.z).length()
		rig.set_locomotion_blend(hspeed)
