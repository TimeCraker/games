extends SceneTree
var t := 0
var tree: AnimationTree
var player: AnimationPlayer
func _initialize() -> void:
	var sm := AnimationNodeStateMachine.new()
	var anim := AnimationNodeAnimation.new()
	anim.animation = "idle"
	sm.add_node("Idle", anim, Vector2(0, 0))
	sm.add_transition("Idle", "Idle", _tr())
	tree = AnimationTree.new()
	tree.tree_root = sm
	tree.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
	var holder := Node3D.new()
	root.add_child(holder)
	player = AnimationPlayer.new()
	holder.add_child(player)
	var lib := AnimationLibrary.new()
	lib.add_animation("idle", Animation.new())
	player.add_animation_library("", lib)
	tree.anim_player = tree.get_path_to(player)  # holder/AnimationTree → holder/AnimationPlayer
	holder.add_child(tree)
	tree.active = true
	print("post-add active=", tree.active)
func _tr() -> AnimationNodeStateMachineTransition:
	var tr := AnimationNodeStateMachineTransition.new()
	tr.advance_mode = AnimationNodeStateMachineTransition.ADVANCE_MODE_AUTO
	return tr
func _physics_process(_d: float) -> bool:
	t += 1
	if t == 2 or t == 10:
		var names: Array = []
		for p in tree.get_property_list():
			if String(p.name).begins_with("parameters/"):
				names.append(p.name)
		print("t=", t, " params=", names.size(), " sample=", names.slice(0, 6))
		print("  playback_obj=", tree.get("parameters/Idle/playback"))
	if t >= 10:
		quit(0)
		return true
	return false
