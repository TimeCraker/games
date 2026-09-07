extends SceneTree
## Aster AnimationTree 状态树构建器（无头运行）：
##   godot --headless --path client-godot-v2 -s scripts/animation/build_aster_animtree.gd
## 输出 res://art/animations/aster_anim_tree.tres。
## 根节点 = 状态机 SM：Locomotion(BlendSpace1D 0→2.8→7.0) + 全部战斗状态，
## 切换统一 0.15~0.20s CrossFade；循环态回 Locomotion 一律禁用 AT_END（防 travel 卡死）。

const OUT_PATH := "res://art/animations/aster_anim_tree.tres"

# 状态名 -> [动画剪辑, 是否循环]
const STATES := {
	"Jump": ["jump", false],
	"Fall": ["fall", true],
	"Land": ["fall-landing", false],
	"Slide": ["crouch-run", true],
	"Dodge": ["Roll", false],
	"WallSlide": ["wall-slide-front", true],
	"Combo1": ["Slash1", false],
	"Combo2": ["Slash2", false],
	"Combo3": ["Slash3", false],
	"Combo4": ["SlashUppercut", false],
	"IaiCharge": ["Guarding", true],
	"IaiSlash": ["SlashRelease", false],
	"Parry": ["GuardParry", false],
	"Plunge": ["HeavyJumpAttack", false],
	"Hurt": ["Hurt1", false],
}


func _initialize() -> void:
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")

	var sm := AnimationNodeStateMachine.new()
	sm.add_node("Locomotion", _build_locomotion(lib), Vector2(0, 0))
	var col := 1
	for state_name: String in STATES:
		var clip: String = STATES[state_name][0]
		assert(lib.has_animation(clip), "aster_animlib 缺少剪辑: " + clip)
		var anim_node := AnimationNodeAnimation.new()
		anim_node.animation = clip
		sm.add_node(state_name, anim_node, Vector2(col * 220, 0))
		col += 1

	# Locomotion <-> 各状态双通过渡（xfade 0.18）
	var xf_loco := 0.18
	for state_name: String in STATES:
		var is_loop: bool = STATES[state_name][1]
		sm.add_transition("Locomotion", state_name, _trans(xf_loco, false))
		# 非循环态走 AT_END 自动回归；循环态只能由驱动器 travel 拉回（AT_END+循环=卡死）
		sm.add_transition(state_name, "Locomotion", _trans(xf_loco, not is_loop))

	# 连招链 Combo1..4 顺序衔接 + 各段 AT_END 回归
	for i in range(1, 4):
		sm.add_transition("Combo%d" % i, "Combo%d" % (i + 1), _trans(0.15, false))
	# 居合蓄力 -> 拔刀释放（快速 0.12s CrossFade，次元斩的利落感）
	sm.add_transition("IaiCharge", "IaiSlash", _trans(0.12, false))
	# 开机入口：Start → Locomotion 自动过渡（否则状态机会直落 End 静止）
	sm.add_transition("Start", "Locomotion", _trans(0.2, false))

	# BlendTree 根 + TimeScale 包装：局部卡肉 = parameters/HitstopScale/scale = 0.0
	#（4.7 AnimationTree 无 speed 属性，TimeScale 是 playback 速度的正规 API）
	var bt := AnimationNodeBlendTree.new()
	bt.add_node("SM", sm, Vector2(0, 0))
	var hitstop_scale := AnimationNodeTimeScale.new()
	bt.add_node("HitstopScale", hitstop_scale, Vector2(280, 0))
	bt.connect_node("HitstopScale", 0, "SM")
	bt.connect_node("output", 0, "HitstopScale")

	var err := ResourceSaver.save(bt, OUT_PATH)
	print("saved %s states=%d transitions=%d err=%d" % [OUT_PATH, sm.get_node_list().size(), sm.get_transition_count(), err])
	quit(0 if err == OK else 1)


func _build_locomotion(_lib: AnimationLibrary) -> AnimationNodeBlendSpace1D:
	var bs := AnimationNodeBlendSpace1D.new()
	bs.min_space = 0.0
	bs.max_space = 7.0
	# 7.0 端点用 LightRunning（标准前倾/抬膝跑姿，符合 12° 前倾评审基线）；
	# Sprint 是深蹲战斗突进（弓背体态），只适合战斗位移不适合常规疾跑
	var points := {"LightIdle": 0.0, "LightWalking": 2.8, "LightRunning": 7.0}
	for clip: String in points:
		var anim_node := AnimationNodeAnimation.new()
		anim_node.animation = clip
		bs.add_blend_point(anim_node, points[clip])
	return bs


func _trans(xfade: float, at_end: bool) -> AnimationNodeStateMachineTransition:
	var t := AnimationNodeStateMachineTransition.new()
	t.xfade_time = xfade
	t.switch_mode = AnimationNodeStateMachineTransition.SWITCH_MODE_IMMEDIATE
	t.advance_mode = AnimationNodeStateMachineTransition.ADVANCE_MODE_AUTO if at_end \
			else AnimationNodeStateMachineTransition.ADVANCE_MODE_ENABLED
	return t
