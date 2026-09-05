class_name FloatingDamageText
extends Label3D

## 3D 伤害飘字组件

func setup(damage: float, is_crit: bool, spawn_pos: Vector3) -> void:
	text = str(int(damage))
	global_position = spawn_pos + Vector3(randf_range(-0.3, 0.3), randf_range(0.2, 0.6), randf_range(-0.3, 0.3))
	billboard = BaseMaterial3D.BILLBOARD_ENABLED
	no_depth_test = true
	
	if is_crit:
		modulate = Color(1.0, 0.85, 0.15, 1.0) # 金黄暴击
		pixel_size = 0.008
	else:
		modulate = Color(0.95, 0.95, 0.95, 1.0) # 纯白轻击
		pixel_size = 0.005

	var tween: Tween = create_tween()
	tween.set_parallel(true)
	tween.tween_property(self, "position:y", position.y + 1.2, 0.75).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "modulate:a", 0.0, 0.75).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tween.finished.connect(queue_free)
