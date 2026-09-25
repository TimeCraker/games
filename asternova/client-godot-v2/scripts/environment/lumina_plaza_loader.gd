class_name LuminaPlazaLoader
extends Node3D

## 动态加载光映广场 1:1 完整大师级场景资产（全套 PBR 水洼解耦石板 + 贴花 + 发光招牌）

const MASTER_GLB = "res://models/lumina_plaza/lumina_plaza_masterpiece_full.glb"

var mat_floor: StandardMaterial3D
var mat_bike: StandardMaterial3D
var mat_sign: StandardMaterial3D
var mat_manhole: StandardMaterial3D
var mat_tactile: StandardMaterial3D
var mat_red_arch: StandardMaterial3D
var mat_cat: StandardMaterial3D

func _ready() -> void:
	print("[LuminaPlaza] Initializing PBR materials for Masterpiece Plaza...")
	_init_materials()
	
	if not FileAccess.file_exists(MASTER_GLB):
		push_warning("[LuminaPlaza] Master GLB not found: " + MASTER_GLB)
		return
	
	var gltf := GLTFDocument.new()
	var state := GLTFState.new()
	var err = gltf.append_from_file(MASTER_GLB, state)
	if err != OK:
		push_error("[LuminaPlaza] Failed to parse GLB: %d" % err)
		return
		
	var scene_node = gltf.generate_scene(state)
	if scene_node:
		scene_node.name = "LuminaPlazaMasterWorld"
		add_child(scene_node)
		_process_node(scene_node)
		print("[LuminaPlaza] 1:1 Masterpiece Plaza loaded and visually calibrated successfully!")

func _init_materials() -> void:
	# 1. 地面 PBR 水洼解耦高精石板材质
	mat_floor = StandardMaterial3D.new()
	mat_floor.albedo_texture = load("res://textures/environment/plaza_slate_albedo.png")
	mat_floor.roughness_texture = load("res://textures/environment/plaza_slate_roughness.png")
	mat_floor.normal_enabled = true
	mat_floor.normal_texture = load("res://textures/environment/plaza_slate_normal.png")
	mat_floor.normal_scale = 1.0
	mat_floor.roughness = 1.0 # 由粗糙度贴图精准调制（水洼 0.08 镜面，石板 0.38 哑光）
	mat_floor.metallic = 0.05
	mat_floor.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	
	# 2. 自行车道半透明喷绘贴花
	mat_bike = StandardMaterial3D.new()
	mat_bike.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_bike.albedo_texture = load("res://textures/decals/bike_lane_decal.png")
	mat_bike.roughness = 0.45
	mat_bike.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat_bike.render_priority = 2
	
	# 3. EZ STUDIO 工业发光门头
	mat_sign = StandardMaterial3D.new()
	mat_sign.albedo_texture = load("res://textures/decals/ez_studio_sign_master.png")
	mat_sign.emission_enabled = true
	mat_sign.emission_texture = load("res://textures/decals/ez_studio_sign_master.png")
	mat_sign.emission = Color(1.0, 1.0, 1.0)
	mat_sign.emission_energy_multiplier = 4.5
	mat_sign.roughness = 0.20
	
	# 4. 同心圆深色铸铁井盖
	mat_manhole = StandardMaterial3D.new()
	mat_manhole.albedo_texture = load("res://textures/decals/manhole_cover_diffuse.png")
	mat_manhole.roughness = 0.28
	mat_manhole.metallic = 0.88
	mat_manhole.normal_enabled = true
	mat_manhole.normal_texture = load("res://textures/decals/manhole_cover_bump.png")
	mat_manhole.normal_scale = 1.2
	mat_manhole.render_priority = 1
	
	# 5. 暖姜黄立体导盲带
	mat_tactile = StandardMaterial3D.new()
	mat_tactile.albedo_texture = load("res://textures/decals/tactile_studs_albedo.png")
	mat_tactile.roughness = 0.50
	mat_tactile.render_priority = 1
	
	# 6. 朱红高光双环雕塑 (Candy-Apple Red)
	mat_red_arch = StandardMaterial3D.new()
	mat_red_arch.albedo_color = Color(0.85, 0.07, 0.05, 1.0)
	mat_red_arch.roughness = 0.16
	mat_red_arch.metallic = 0.22
	mat_red_arch.clearcoat_enabled = true
	mat_red_arch.clearcoat = 0.45
	
	# 7. 伴跑奶油白猫咪
	mat_cat = StandardMaterial3D.new()
	mat_cat.albedo_color = Color(0.96, 0.94, 0.90, 1.0)
	mat_cat.roughness = 0.58

func _process_node(node: Node) -> void:
	if node is MeshInstance3D:
		var n_lower = node.name.to_lower()
		
		# 隐藏 GLB 中遗留的孤立武器模型
		if "katana" in n_lower or "blade" in n_lower or "scabbard" in n_lower:
			node.visible = false
			return
		
		# 精准材质绑定
		if "plaza_floor" in n_lower or "floor" in n_lower:
			node.set_surface_override_material(0, mat_floor)
			node.create_trimesh_collision()
		elif "bikelane" in n_lower or "bike_lane" in n_lower:
			node.set_surface_override_material(0, mat_bike)
		elif "ez_signboard" in n_lower or "signboard" in n_lower:
			node.set_surface_override_material(0, mat_sign)
		elif "manhole" in n_lower:
			node.set_surface_override_material(0, mat_manhole)
		elif "tactile" in n_lower:
			node.set_surface_override_material(0, mat_tactile)
		elif "monument" in n_lower or "redarch" in n_lower:
			node.set_surface_override_material(0, mat_red_arch)
			node.create_trimesh_collision()
		elif "cat" in n_lower:
			node.set_surface_override_material(0, mat_cat)
		elif "building" in n_lower or "tower" in n_lower or "curb" in n_lower or "platform" in n_lower:
			node.create_trimesh_collision()
			
	for child in node.get_children():
		_process_node(child)



