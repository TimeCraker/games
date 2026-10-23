extends Node

## 光照预设对比截图：每个预设 × 每个机位存一张 JPG，然后退出。
## 用法：Godot --path client-godot-v2 res://tests/lighting_preview.tscn -- --out=<目录> [--presets=day_clear,night_city]

const SHOTS := [
	{"name": "store_interior", "from": Vector3(-12.45, 1.62, 21.9), "to": Vector3(-17.25, 1.05, 20.6), "fov": 48.0},
	{"name": "street", "from": Vector3(1.2, 1.7, 28.2), "to": Vector3(-2.6, 1.1, 14.5), "fov": 44.0},
]
const SETTLE_FRAMES := 150

@export var scene: PackedScene
## 站在店门前的角色，用来同时检查角色受光
@export var character: PackedScene
@export var character_position := Vector3(-15.6, 0.0, 21.0)
@export var character_yaw_deg := -70.0


func _ready() -> void:
	var out_dir := OS.get_user_data_dir()
	var only: PackedStringArray = []
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			out_dir = arg.trim_prefix("--out=")
		elif arg.begins_with("--presets="):
			only = arg.trim_prefix("--presets=").split(",")
	DirAccess.make_dir_recursive_absolute(out_dir)

	var level := scene.instantiate()
	add_child(level)
	if character:
		var holder := Node3D.new()
		level.add_child(holder)
		holder.position = character_position
		holder.rotation_degrees.y = character_yaw_deg
		holder.add_child(character.instantiate())
	var rig := level.get_node("LightingRig") as LightingRig
	var camera := Camera3D.new()
	level.add_child(camera)
	camera.current = true

	for preset: LightingPreset in rig.presets:
		var key := preset.resource_path.get_file().get_basename()
		if not only.is_empty() and key not in only:
			continue
		rig.preset = preset
		for shot in SHOTS:
			camera.look_at_from_position(shot["from"], shot["to"])
			camera.fov = shot["fov"]
			for i in SETTLE_FRAMES:
				await get_tree().process_frame
			await RenderingServer.frame_post_draw
			var path := "%s/%s_%s.jpg" % [out_dir, key, shot["name"]]
			get_viewport().get_texture().get_image().save_jpg(path, 0.9)
			print("[lighting] saved ", path)
	get_tree().quit(0)
