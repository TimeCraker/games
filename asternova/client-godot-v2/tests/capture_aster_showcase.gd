extends SceneTree

const OUT_DIR := "C:/Users/TimeCraker/.gemini/antigravity/brain/a12a34db-37fe-4516-b01d-a4f467888558/"

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	
	var stage := Node3D.new()
	stage.name = "ShowcaseStage"
	root.add_child(stage)
	
	# 1. 摄影棚柔和冷灰环境
	var world_env := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.18, 0.20, 0.24, 1.0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.75, 0.8, 0.9, 1.0)
	env.ambient_light_energy = 1.0
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world_env.environment = env
	stage.add_child(world_env)
	
	# 2. 定向主光源 (斜上方照射，产生清晰投影)
	var sun := DirectionalLight3D.new()
	sun.name = "SunLight"
	sun.transform.basis = Basis(Quaternion(Vector3.UP, deg_to_rad(45.0)) * Quaternion(Vector3.RIGHT, deg_to_rad(-45.0)))
	sun.light_color = Color(1.0, 0.98, 0.95)
	sun.light_energy = 1.6
	sun.shadow_enabled = true
	sun.shadow_bias = 0.005
	sun.shadow_normal_bias = 0.5
	stage.add_child(sun)

	# 补光 Fill Light
	var fill := DirectionalLight3D.new()
	fill.name = "FillLight"
	fill.transform.basis = Basis(Quaternion(Vector3.UP, deg_to_rad(-135.0)) * Quaternion(Vector3.RIGHT, deg_to_rad(-25.0)))
	fill.light_color = Color(0.7, 0.85, 1.0)
	fill.light_energy = 0.8
	fill.shadow_enabled = false
	stage.add_child(fill)
	
	# 3. 高精度网格地面 (Y=0)
	var ground_mesh := PlaneMesh.new()
	ground_mesh.size = Vector2(20, 20)
	var ground_inst := MeshInstance3D.new()
	ground_inst.mesh = ground_mesh
	var ground_mat := StandardMaterial3D.new()
	ground_mat.albedo_color = Color(0.38, 0.40, 0.45)
	ground_mat.roughness = 0.7
	ground_inst.material_override = ground_mat
	stage.add_child(ground_inst)
	
	# 4. 实例化 CharacterAster (包含完整 AsterRig、AnimationTree、Toon 着色器)
	var aster_scene: PackedScene = load("res://scenes/entities/character_aster.tscn")
	var rig: AsterRig = aster_scene.instantiate()
	stage.add_child(rig)
	rig.position = Vector3.ZERO
	
	var cam := Camera3D.new()
	cam.current = true
	cam.fov = 36.0
	stage.add_child(cam)
	
	# 等待 40 帧让 AnimationTree 状态机进入 Locomotion 并完成融合
	for i in range(40):
		await process_frame

	# ==================== 镜头 1: 正面全身待命态 (LightIdle, blend=0.0) ====================
	rig.set_locomotion_blend(0.0)
	for i in range(25):
		await process_frame
	cam.position = Vector3(0.0, 0.85, -2.6)
	cam.look_at(Vector3(0.0, 0.85, 0.0), Vector3.UP)
	for i in range(10):
		await process_frame
	_save_screen("showcase_01_idle_front_full.png")

	# ==================== 镜头 2: 半身上装与腰手特写 ====================
	cam.position = Vector3(0.0, 1.05, -1.4)
	cam.look_at(Vector3(0.0, 0.98, 0.0), Vector3.UP)
	for i in range(10):
		await process_frame
	_save_screen("showcase_02_idle_upper_closeup.png")

	# ==================== 镜头 3: 足底踏地与地面阴影特写 ====================
	cam.position = Vector3(0.0, 0.35, -1.3)
	cam.look_at(Vector3(0.0, 0.10, 0.0), Vector3.UP)
	for i in range(10):
		await process_frame
	_save_screen("showcase_03_idle_grounding_feet.png")

	# ==================== 镜头 4: 侧面行走态 (LightWalking, blend=2.4) ====================
	rig.set_locomotion_blend(2.4)
	for i in range(35):
		await process_frame
	cam.position = Vector3(-2.6, 0.85, 0.0)
	cam.look_at(Vector3(0.0, 0.85, 0.0), Vector3.UP)
	for i in range(10):
		await process_frame
	_save_screen("showcase_04_walk_side.png")

	# ==================== 镜头 5: 背后追尾奔跑态 (LightRunning, blend=5.0) ====================
	rig.set_locomotion_blend(5.0)
	for i in range(35):
		await process_frame
	cam.position = Vector3(0.0, 1.15, 2.5)
	cam.look_at(Vector3(0.0, 0.85, 0.0), Vector3.UP)
	for i in range(10):
		await process_frame
	_save_screen("showcase_05_run_back.png")

	print("[Showcase] Full real-game showcase clips captured successfully!")
	quit(0)

func _save_screen(filename: String) -> void:
	var img := root.get_texture().get_image()
	if img:
		var target_path := OUT_DIR + filename
		var err := img.save_png(target_path)
		print("[Showcase] Saved ", filename, " err=", err)
	else:
		push_error("[Showcase] Viewport texture image is null!")
