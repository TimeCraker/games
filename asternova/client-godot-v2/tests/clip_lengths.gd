extends SceneTree
func _initialize() -> void:
	var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	for n in ["idle", "walk", "run_067", "jump", "fall", "fall-landing", "crouch-run",
			"wall-slide-front", "Roll", "Slash1", "Slash2", "Slash3", "SlashUppercut",
			"SlashCharge", "SlashRelease", "Guarding", "GuardParry", "Hurt1", "HeavyJumpAttack",
			"LightIdle", "LightWalking", "LightRunning", "Sprint"]:
		if lib.has_animation(n):
			var a: Animation = lib.get_animation(n)
			print("%-18s len=%.3f loop=%d tracks=%d" % [n, a.length, a.loop_mode, a.get_track_count()])
		else:
			print("%-18s MISSING" % n)
	quit(0)
