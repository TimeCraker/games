extends SceneTree

func _initialize() -> void:
	var melee: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var anims := melee.get_animation_list()
	print("MeleeLib anims total: ", anims.size())
	
	var attack_anims: Array[String] = []
	for a in anims:
		if a.to_lower().contains("slash") or a.to_lower().contains("attack") or a.to_lower().contains("sword") or a.to_lower().contains("combo"):
			attack_anims.append(a)
	
	print("Attack/Slash anims: ", attack_anims)
	
	# 检查 Slash1 的轨迹长度、骨骼轨道
	for name in ["Slash1", "Combo1"]:
		if melee.has_animation(name):
			var anim := melee.get_animation(name)
			print("Anim %s: len=%.2fs tracks=%d" % [name, anim.length, anim.get_track_count()])
			for t in anim.get_track_count():
				var path := anim.track_get_path(t)
				if path.get_subname_count() > 0:
					var bname := path.get_subname(0)
					if bname in ["Hips", "LeftUpperLeg", "RightUpperLeg"]:
						var track_type := anim.track_get_type(t)
						print("  Track %s type=%d keys=%d" % [path, track_type, anim.track_get_key_count(t)])

	quit(0)
