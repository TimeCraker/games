extends SceneTree
func _initialize() -> void:
	for cls in ["AnimationNodeAnimation", "AnimationNodeTimeScale", "AnimationNodeBlendSpace1D", "AnimationNodeStateMachine", "AnimationNodeStateMachineTransition", "AnimationNodeOutput", "AnimationTree"]:
		var props := ClassDB.class_get_property_list(cls, true)
		var names: Array = []
		for p in props:
			if not String(p.name).begins_with("resource") and p.name != "script":
				names.append(String(p.name))
		print(cls, " props: ", names)
	for cls in ["AnimationNodeBlendSpace1D", "AnimationNodeStateMachine", "AnimationNodeStateMachineTransition"]:
		var methods: Array = []
		for m in ClassDB.class_get_method_list(cls, true):
			methods.append(String(m.name))
		print(cls, " methods: ", methods)
	quit(0)
