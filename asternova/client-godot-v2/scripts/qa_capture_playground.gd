extends Node

var frame: int = 0
var out_dir := "C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165"

func _process(_delta: float) -> void:
	frame += 1
	var stage := get_tree().current_scene
	var player = stage.get_node_or_null("Player") if stage else null
	
	if frame == 50:
		# 待命态截图
		_save("real_game_combat_idle.png")
	elif frame == 55:
		# 驱动前进移动
		if player:
			var rig = player.get_node_or_null("VisualRoot/CharacterAster")
			if rig:
				rig.set_locomotion_blend(4.5)
			player.velocity = Vector3(0, 0, -4.5)
	elif frame == 95:
		# 移动态截图
		_save("real_game_combat_run.png")
	elif frame == 100:
		get_tree().quit(0)

func _save(fname: String) -> void:
	var img := get_viewport().get_texture().get_image()
	if img:
		img.save_png(out_dir + "/" + fname)
		print("[QA] Saved " + fname)
