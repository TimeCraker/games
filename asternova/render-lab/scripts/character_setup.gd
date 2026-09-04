extends Node3D

@onready var skeleton: Skeleton3D = $Skeleton3D
@onready var face_mesh: MeshInstance3D = $Skeleton3D/Face
@onready var body_mesh: MeshInstance3D = $Skeleton3D/Body
@onready var hair_mesh: MeshInstance3D = $Skeleton3D/Hair001

const SHADER_TOON = preload("res://shaders/toon_character.gdshader")
const SHADER_FACE = preload("res://shaders/toon_face.gdshader")
const SHADER_OUTLINE = preload("res://shaders/outline.gdshader")

func _ready() -> void:
	print("--- character_setup _ready called! ---")
	print("skeleton=", skeleton, " face=", face_mesh, " body=", body_mesh, " hair=", hair_mesh)
	_setup_materials()
	_setup_pose()

func _create_outline_pass(color: Color = Color(0.26, 0.28, 0.38, 1.0), thickness: float = 0.0028) -> ShaderMaterial:
	var outline_mat := ShaderMaterial.new()
	outline_mat.render_priority = 1
	outline_mat.shader = SHADER_OUTLINE
	outline_mat.set_shader_parameter("outline_color", color)
	outline_mat.set_shader_parameter("outline_thickness", thickness)
	outline_mat.set_shader_parameter("distance_scaling", true)
	return outline_mat

func _create_toon_mat(tex: Texture2D, albedo: Color = Color(1, 1, 1, 1), outline: bool = true, outline_color: Color = Color(0.24, 0.26, 0.36, 1.0), desat: float = 0.0, rim: bool = true, alpha_scissor: bool = false, normal_tex: Texture2D = null, nml_depth: float = 1.0) -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.render_priority = 0
	mat.shader = SHADER_TOON
	mat.set_shader_parameter("albedo_color", albedo)
	mat.set_shader_parameter("albedo_texture", tex)
	mat.set_shader_parameter("desaturation", desat)
	mat.set_shader_parameter("use_alpha_scissor", alpha_scissor)
	mat.set_shader_parameter("alpha_scissor_threshold", 0.5)
	
	if normal_tex:
		mat.set_shader_parameter("use_normal_map", true)
		mat.set_shader_parameter("normal_texture", normal_tex)
		mat.set_shader_parameter("normal_depth", nml_depth)
	
	# 日系冷蓝/淡紫赛璐璐二阶阴影 (STYLE.md 规范)
	mat.set_shader_parameter("shadow_tint", Color(0.72, 0.76, 0.88, 1.0))
	mat.set_shader_parameter("ramp_threshold", 0.48)
	mat.set_shader_parameter("ramp_smoothness", 0.03)
	mat.set_shader_parameter("shadow_strength", 0.60)
	
	mat.set_shader_parameter("enable_rim", rim)
	mat.set_shader_parameter("rim_color", Color(0.68, 0.82, 0.98, 1.0)) # STYLE.md 冷蓝高光/边缘光
	mat.set_shader_parameter("rim_threshold", 0.65)
	mat.set_shader_parameter("rim_smoothness", 0.04)
	mat.set_shader_parameter("rim_spread", 2.2)
	
	mat.set_shader_parameter("specular_color", Color(0.92, 0.95, 1.0, 1.0))
	mat.set_shader_parameter("specular_size", 0.06)
	mat.set_shader_parameter("specular_smoothness", 0.015)
	
	if outline:
		mat.next_pass = _create_outline_pass(outline_color, 0.0026)
	return mat

func _setup_materials() -> void:
	# 1. 贴图加载
	var tex_face: Texture2D = load("res://models/aster/aster_model_F00_000_Face_00.png")
	var tex_body: Texture2D = load("res://models/aster/aster_model_F00_002_Body_00.png")
	var tex_clothes: Texture2D = load("res://models/aster/aster_model_F00_002_Onepiece_01.png")
	var tex_shoes: Texture2D = load("res://models/aster/aster_model_F00_002_Shoes_01.png")
	var tex_hair_back: Texture2D = load("res://models/aster/aster_model_F00_000_HairBack_00.png")
	var tex_hair1: Texture2D = load("res://models/aster/aster_model_F00_000_Hair_00_01.png")
	var tex_hair2: Texture2D = load("res://models/aster/aster_model_F00_000_Hair_00_02.png")
	var tex_hair3: Texture2D = load("res://models/aster/aster_model_F00_000_Hair_00_03.png")

	# 法线贴图 (衣褶布纹与发丝结构)
	var tex_clothes_nml: Texture2D = load("res://models/aster/aster_model_F00_002_02_Body_00_nml.png")
	var tex_hair_nml: Texture2D = load("res://models/aster/aster_model_F00_000_Hair_00_nml.png")
	var tex_hair_back_nml: Texture2D = load("res://models/aster/aster_model_F00_000_HairBack_00_nml.png")

	# 2. 面部材质 (消除粗糙暗影，呈现细腻通透冷白肌与淡粉腮红)
	if face_mesh:
		var mat_face_skin := ShaderMaterial.new()
		mat_face_skin.shader = SHADER_FACE
		mat_face_skin.set_shader_parameter("skin_color", Color(1.0, 0.98, 0.97, 1.0))
		mat_face_skin.set_shader_parameter("face_shadow_tint", Color(0.92, 0.88, 0.95, 1.0))
		mat_face_skin.set_shader_parameter("shadow_threshold", 0.45)
		mat_face_skin.set_shader_parameter("shadow_softness", 0.03)
		mat_face_skin.set_shader_parameter("face_texture", tex_face)
		mat_face_skin.next_pass = _create_outline_pass(Color(0.35, 0.28, 0.35, 1.0), 0.0020)
		
		# 面部皮肤槽位 (7 和 8)
		face_mesh.set_surface_override_material(7, mat_face_skin)
		face_mesh.set_surface_override_material(8, mat_face_skin)

	# 3. 身体与服装
	if body_mesh:
		var mat_body_skin = _create_toon_mat(tex_body, Color(0.96, 0.94, 0.93), false, Color(), 0.0, false, false)
		mat_body_skin.set_shader_parameter("shadow_tint", Color(0.85, 0.80, 0.88, 1.0))
		for i in range(4):
			body_mesh.set_surface_override_material(i, mat_body_skin)
		
		# 服装 (象牙白常服 + 层次下摆 + 樱粉衬裙 + 衣褶法线，基色 0.88 保持最高光斑受光不溢出)
		var mat_clothes = _create_toon_mat(tex_clothes, Color(0.88, 0.88, 0.92), true, Color(0.24, 0.26, 0.38), 0.0, true, true, tex_clothes_nml, 1.2)
		body_mesh.set_surface_override_material(4, mat_clothes)
		
		# 鞋履 (白色玛丽珍圆头鞋)
		var mat_shoes = _create_toon_mat(tex_shoes, Color(0.90, 0.90, 0.94), true, Color(0.26, 0.28, 0.38), 0.0, true, false)
		body_mesh.set_surface_override_material(5, mat_shoes)
		
		# 脑后发束 (珍珠银白 + 冷蓝高光)
		var mat_back_hair = _create_toon_mat(tex_hair_back, Color(0.94, 0.95, 0.98), true, Color(0.26, 0.30, 0.42), 0.0, true, false, tex_hair_back_nml, 0.9)
		body_mesh.set_surface_override_material(6, mat_back_hair)

	# 4. 头发材质 (珍珠银白长发 + 樱粉渐变发尾 + 青绿发饰发带)
	if hair_mesh:
		var mat_hair1 = _create_toon_mat(tex_hair1, Color(0.94, 0.95, 0.98), true, Color(0.26, 0.30, 0.42), 0.0, true, true, tex_hair_nml, 0.9)
		var mat_hair2 = _create_toon_mat(tex_hair2, Color(0.94, 0.95, 0.98), true, Color(0.26, 0.30, 0.42), 0.0, true, true, tex_hair_nml, 0.9)
		var mat_ribbon = _create_toon_mat(tex_hair3, Color(1.0, 1.0, 1.0), true, Color(0.18, 0.32, 0.30), 0.0, true, false)
		
		for s in range(hair_mesh.mesh.get_surface_count()):
			if s in [53, 54, 55, 56, 57]:
				hair_mesh.set_surface_override_material(s, mat_ribbon)
			elif s >= 15 and s <= 24:
				hair_mesh.set_surface_override_material(s, mat_hair2)
			else:
				hair_mesh.set_surface_override_material(s, mat_hair1)
	print("Finished _setup_materials! Body s4 override: ", body_mesh.get_surface_override_material(4) if body_mesh else "null")

func _setup_pose() -> void:
	if not skeleton:
		return
	
	# 姿态：优雅文静的二次元自然立姿 (Natural anime A-pose)
	var left_arm: int = skeleton.find_bone("J_Bip_L_UpperArm")
	var right_arm: int = skeleton.find_bone("J_Bip_R_UpperArm")
	var left_forearm: int = skeleton.find_bone("J_Bip_L_LowerArm")
	var right_forearm: int = skeleton.find_bone("J_Bip_R_LowerArm")
	var left_hand: int = skeleton.find_bone("J_Bip_L_Hand")
	var right_hand: int = skeleton.find_bone("J_Bip_R_Hand")
	var head: int = skeleton.find_bone("J_Bip_C_Head")
	var spine: int = skeleton.find_bone("J_Bip_C_Spine")
	
	# 左臂自然下垂：左臂骨骼沿 -X 轴，旋转 +Z 为下摆
	if left_arm != -1:
		var q_arm := Quaternion.from_euler(Vector3(deg_to_rad(6.0), deg_to_rad(-10.0), deg_to_rad(66.0)))
		skeleton.set_bone_pose_rotation(left_arm, q_arm)
	if left_forearm != -1:
		var q_fa := Quaternion.from_euler(Vector3(deg_to_rad(0.0), deg_to_rad(-8.0), deg_to_rad(12.0)))
		skeleton.set_bone_pose_rotation(left_forearm, q_fa)
	if left_hand != -1:
		var q_hand := Quaternion.from_euler(Vector3(deg_to_rad(0.0), deg_to_rad(-4.0), deg_to_rad(6.0)))
		skeleton.set_bone_pose_rotation(left_hand, q_hand)
		
	# 右臂自然下垂：右臂骨骼沿 +X 轴，旋转 -Z 为下摆
	if right_arm != -1:
		var q_arm_r := Quaternion.from_euler(Vector3(deg_to_rad(-6.0), deg_to_rad(10.0), deg_to_rad(-66.0)))
		skeleton.set_bone_pose_rotation(right_arm, q_arm_r)
	if right_forearm != -1:
		var q_fa_r := Quaternion.from_euler(Vector3(deg_to_rad(0.0), deg_to_rad(8.0), deg_to_rad(-12.0)))
		skeleton.set_bone_pose_rotation(right_forearm, q_fa_r)
	if right_hand != -1:
		var q_hand_r := Quaternion.from_euler(Vector3(deg_to_rad(0.0), deg_to_rad(4.0), deg_to_rad(-6.0)))
		skeleton.set_bone_pose_rotation(right_hand, q_hand_r)
		
	# 头部与脊柱微调（轻微偏头与亭亭玉立的挺拔仪态）
	if head != -1:
		var q_head := Quaternion.from_euler(Vector3(deg_to_rad(-2.0), deg_to_rad(-3.0), deg_to_rad(2.5)))
		skeleton.set_bone_pose_rotation(head, q_head)
	if spine != -1:
		var q_spine := Quaternion.from_euler(Vector3(deg_to_rad(-2.0), deg_to_rad(0.0), deg_to_rad(0.0)))
		skeleton.set_bone_pose_rotation(spine, q_spine)
