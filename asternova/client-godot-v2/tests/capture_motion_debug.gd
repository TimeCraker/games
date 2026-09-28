extends SceneTree

var frame_count := 0
var char_aster: AsterRig = null
var cam: Camera3D = null
var anim_player: AnimationPlayer = null

func _initialize() -> void:
	var root = get_root()
	
	# Create 3D world environment
	var env_node = WorldEnvironment.new()
	var env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.18, 0.20, 0.24)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.6, 0.65, 0.7)
	env.ambient_light_energy = 1.0
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env_node.environment = env
	root.add_child(env_node)

	var light = DirectionalLight3D.new()
	light.light_color = Color(1.0, 0.98, 0.95)
	light.light_energy = 1.0
	light.rotation_degrees = Vector3(-35, 45, 0)
	root.add_child(light)

	var ground = MeshInstance3D.new()
	var plane = PlaneMesh.new()
	plane.size = Vector2(20, 20)
	ground.mesh = plane
	var gmat = StandardMaterial3D.new()
	gmat.albedo_color = Color(0.25, 0.28, 0.32)
	ground.material_override = gmat
	root.add_child(ground)

	var path := "res://scenes/entities/character_aster.tscn"
	char_aster = load(path).instantiate() as AsterRig
	root.add_child(char_aster)
	char_aster.position = Vector3(0, 0, 0)

	cam = Camera3D.new()
	cam.current = true
	root.add_child(cam)

	# Locate animation player
	anim_player = char_aster.find_child("AnimationPlayer", true, false) as AnimationPlayer
	print("Found AnimationPlayer: ", anim_player != null)

	# Start process loop
	root.process_mode = Node.PROCESS_MODE_ALWAYS

func _physics_process(_delta: float) -> bool:
	frame_count += 1
	var vp = get_root().get_viewport()
	
	if frame_count == 5:
		# View 1: Idle front full body
		cam.position = Vector3(0, 1.0, 2.5)
		cam.look_at(Vector3(0, 0.85, 0), Vector3.UP)
	elif frame_count == 6:
		var img = vp.get_texture().get_image()
		img.save_png("res://tests/debug_motion_01_idle_front.png")
		print("Saved debug_motion_01_idle_front.png")

		# Switch to LightWalking
		if anim_player and anim_player.has_animation("aster_animlib/LightWalking"):
			anim_player.play("aster_animlib/LightWalking")
			anim_player.seek(0.3, true)
		elif anim_player and anim_player.has_animation("LightWalking"):
			anim_player.play("LightWalking")
			anim_player.seek(0.3, true)
			
		cam.position = Vector3(-1.8, 0.8, 1.2)
		cam.look_at(Vector3(0, 0.75, 0), Vector3.UP)

	elif frame_count == 10:
		var img = vp.get_texture().get_image()
		img.save_png("res://tests/debug_motion_02_walk_stride.png")
		print("Saved debug_motion_02_walk_stride.png")

		# Switch to LightRunning
		if anim_player and anim_player.has_animation("aster_animlib/LightRunning"):
			anim_player.play("aster_animlib/LightRunning")
			anim_player.seek(0.4, true)
		elif anim_player and anim_player.has_animation("LightRunning"):
			anim_player.play("LightRunning")
			anim_player.seek(0.4, true)

		cam.position = Vector3(-2.2, 0.7, 0.5)
		cam.look_at(Vector3(0, 0.75, 0), Vector3.UP)

	elif frame_count == 15:
		var img = vp.get_texture().get_image()
		img.save_png("res://tests/debug_motion_03_run_stride.png")
		print("Saved debug_motion_03_run_stride.png")

		# View back
		cam.position = Vector3(0, 1.0, -2.5)
		cam.look_at(Vector3(0, 0.85, 0), Vector3.UP)

	elif frame_count == 18:
		var img = vp.get_texture().get_image()
		img.save_png("res://tests/debug_motion_04_run_back.png")
		print("Saved debug_motion_04_run_back.png")
		quit(0)
	return false
