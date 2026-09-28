extends SceneTree

## 跑步剪辑体态对比探针：绕开 AnimationTree，直接在 rig 的 AnimationPlayer 上
## 逐剪辑播放并各抓 3 张周期相位帧，供选型 BlendSpace 7.0 端点。

const OUT_DIR := "res://../art/render_previews/combat"
const CLIPS := ["LightRunning", "HeavyRunning", "run_067", "Sprint", "LightWalking", "sneak-run"]

var player: CharacterBody3D = null
var cam: Camera3D = null
var images: Dictionary = {}

func _initialize() -> void:
	root.size = Vector2i(2048, 1152)
	var scene: Node = (load("res://scenes/levels/combat_playground.tscn") as PackedScene).instantiate()
	root.add_child(scene)
	_main(scene)

func _main(scene: Node) -> void:
	await ticks(4)
	root.mode = Window.MODE_WINDOWED
	root.size = Vector2i(2048, 1152)
	await ticks(2)
	player = scene.get_node("Player")
	# 关动画树，改用 AnimationPlayer 直驱
	var rig: Node = player.visual_root.get_node("CharacterAster")
	var tree: AnimationTree = null
	for n in rig.find_children("*", "AnimationTree", true, false):
		tree = n
	if tree:
		tree.active = false
	var ap: AnimationPlayer = null
	for n in rig.find_children("*", "AnimationPlayer", true, false):
		ap = n
	print("[probe] anim_player=", ap, " lib_names=", ap.get_animation_list().slice(0, 5))
	# endfield 布光
	var studio: Node3D = (load("res://scenes/lighting/endfield_lighting_studio.tscn") as PackedScene).instantiate()
	scene.add_child(studio)
	var old_we: WorldEnvironment = scene.get_node_or_null("WorldEnvironment")
	if old_we:
		old_we.environment = load("res://environments/endfield_studio_environment.tres")
	var old_sun: DirectionalLight3D = scene.get_node_or_null("DirectionalLight3D")
	if old_sun:
		old_sun.visible = false
	var hud: Node = scene.get_node_or_null("HUDLayer")
	if hud:
		hud.visible = false
	for lbl in scene.find_children("*", "Label3D", true, false):
		(lbl as Label3D).visible = false
	player.camera_controller.process_mode = Node.PROCESS_MODE_DISABLED
	cam = Camera3D.new()
	root.add_child(cam)
	cam.fov = 42.0
	cam.make_current()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))

	for clip_name: String in CLIPS:
		if not ap.has_animation(clip_name):
			print("[probe] 缺剪辑: ", clip_name)
			continue
		var a: Animation = ap.get_animation(clip_name)
		ap.play(clip_name, 0.2, 1.0)
		await ticks(40)  # 收敛
		var phase := 0.0
		for i in 3:
			phase = a.length * (0.1 + 0.3 * i)
			ap.seek(phase, true)
			await ticks(3)
			cam.global_position = player.global_position + Vector3(2.9, 1.15, 0.35)
			cam.look_at(player.global_position + Vector3(0, 0.95, 0))
			await RenderingServer.frame_post_draw
			var img := root.get_viewport().get_texture().get_image()
			images["probe_%s_%d" % [clip_name, i]] = img
			print("[probe] %s phase=%.2f captured" % [clip_name, phase])
	ap.pause()
	for name: String in images:
		images[name].save_png(ProjectSettings.globalize_path("%s/%s.png" % [OUT_DIR, name]))
	print("PROBE_DONE count=%d" % images.size())
	quit(0)

func ticks(n: int) -> void:
	for i in n:
		await physics_frame
