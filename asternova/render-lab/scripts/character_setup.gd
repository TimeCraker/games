extends Node3D

var skeleton: Skeleton3D
var face_mesh: MeshInstance3D
var body_mesh: MeshInstance3D
var hair_mesh: MeshInstance3D

const SHADER_TOON = preload("res://shaders/toon_character.gdshader")
const SHADER_FACE = preload("res://shaders/toon_face.gdshader")
const SHADER_HAIR = preload("res://shaders/toon_hair.gdshader")
const SHADER_OUTLINE = preload("res://shaders/outline.gdshader")

func _ready() -> void:
	skeleton = find_child("Skeleton3D", true, false)
	face_mesh = find_child("Face", true, false)
	body_mesh = find_child("Body", true, false)
	hair_mesh = find_child("Hair001", true, false)
	print("--- character_setup _ready called! ---")
	print("skeleton=", skeleton, " face=", face_mesh, " body=", body_mesh, " hair=", hair_mesh)
	_setup_materials()
	_setup_pose()

func _create_outline_pass(color: Color = Color(0.24, 0.26, 0.36, 1.0), thickness: float = 0.0022) -> ShaderMaterial:
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
	
	# 日系柔和淡紫赛璐璐二阶阴影 (STYLE.md 规范)
	mat.set_shader_parameter("shadow_tint", Color(0.82, 0.84, 0.92, 1.0))
	mat.set_shader_parameter("ramp_threshold", 0.48)
	mat.set_shader_parameter("ramp_smoothness", 0.04)
	mat.set_shader_parameter("shadow_strength", 0.45)
	
	mat.set_shader_parameter("enable_rim", rim)
	mat.set_shader_parameter("rim_color", Color(0.85, 0.92, 1.0, 1.0))
	mat.set_shader_parameter("rim_threshold", 0.65)
	mat.set_shader_parameter("rim_smoothness", 0.04)
	mat.set_shader_parameter("rim_spread", 2.2)
	
	mat.set_shader_parameter("specular_color", Color(0.95, 0.97, 1.0, 1.0))
	mat.set_shader_parameter("specular_size", 0.05)
	mat.set_shader_parameter("specular_smoothness", 0.015)
	
	if outline:
		mat.next_pass = _create_outline_pass(outline_color, 0.0022)
	return mat

func _create_hair_mat(tex: Texture2D) -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.render_priority = 0
	mat.shader = SHADER_HAIR
	mat.set_shader_parameter("albedo_color", Color(1.0, 1.0, 1.0, 1.0))
	mat.set_shader_parameter("albedo_texture", tex)
	mat.set_shader_parameter("shadow_tint", Color(0.82, 0.84, 0.92, 1.0))
	mat.set_shader_parameter("ramp_threshold", 0.46)
	mat.set_shader_parameter("ramp_smoothness", 0.04)
	mat.set_shader_parameter("shadow_strength", 0.40)
	mat.set_shader_parameter("enable_rim", true)
	mat.set_shader_parameter("rim_color", Color(0.88, 0.93, 1.0, 1.0))
	mat.set_shader_parameter("rim_threshold", 0.62)
	return mat

func _setup_materials() -> void:
	# 1. 贴图加载
	var tex_face: Texture2D = load("res://models/aster/aster_model_F00_000_Face_00.png")
	var tex_iris: Texture2D = load("res://models/aster/aster_model_F00_000_EyeIris_00.png")
	var tex_hl: Texture2D = load("res://models/aster/aster_model_F00_000_EyeHighlight_00.png")
	var tex_ew: Texture2D = load("res://models/aster/aster_model_F00_000_EyeWhite_00.png")
	var tex_eyeline: Texture2D = load("res://models/aster/aster_model_F00_000_FaceEyeline_00.png")
	var tex_elash: Texture2D = load("res://models/aster/aster_model_F00_000_FaceEyelash_00.png")
	var tex_brow: Texture2D = load("res://models/aster/aster_model_F00_000_FaceBrow_00.png")
	var tex_mouth: Texture2D = load("res://models/aster/aster_model_F00_000_FaceMouth_00.png")
	
	var tex_body: Texture2D = load("res://models/aster/aster_model_F00_002_Body_00.png")
	var tex_clothes: Texture2D = load("res://models/aster/aster_model_F00_002_Onepiece_01.png")
	var tex_shoes: Texture2D = load("res://models/aster/aster_model_F00_002_Shoes_01.png")
	var tex_hair_back: Texture2D = load("res://models/aster/aster_model_F00_000_HairBack_00.png")
	var tex_hair1: Texture2D = load("res://models/aster/aster_model_F00_000_Hair_00_01.png")
	var tex_hair2: Texture2D = load("res://models/aster/aster_model_F00_000_Hair_00_02.png")
	var tex_hair3: Texture2D = load("res://models/aster/aster_model_F00_000_Hair_00_03.png")

	# 法线贴图 (衣褶布纹与发丝结构)
	var tex_clothes_nml: Texture2D = load("res://models/aster/aster_model_F00_002_02_Body_00_nml.png")

	# 2. 面部全槽位材质覆盖 (彻底还原 Aster 招牌二次元容颜)
	if face_mesh:
		# Slot 0: FaceMouth
		var mat_mouth := StandardMaterial3D.new()
		mat_mouth.shading_mode = StandardMaterial3D.SHADING_MODE_PER_PIXEL
		mat_mouth.albedo_texture = tex_mouth
		face_mesh.set_surface_override_material(0, mat_mouth)

		# Slot 1: EyeWhite (柔和眼部阴影)
		var mat_ew := StandardMaterial3D.new()
		mat_ew.shading_mode = StandardMaterial3D.SHADING_MODE_PER_PIXEL
		mat_ew.albedo_texture = tex_ew
		face_mesh.set_surface_override_material(1, mat_ew)

		# Slot 2: FaceEyeline (柔和优雅杏仁上眼线)
		var mat_eyeline := StandardMaterial3D.new()
		mat_eyeline.transparency = StandardMaterial3D.TRANSPARENCY_ALPHA
		mat_eyeline.cull_mode = StandardMaterial3D.CULL_DISABLED
		mat_eyeline.shading_mode = StandardMaterial3D.SHADING_MODE_UNSHADED
		mat_eyeline.albedo_texture = tex_eyeline
		face_mesh.set_surface_override_material(2, mat_eyeline)

		# Slot 3: FaceEyelash (优雅自然杏仁上睫毛)
		var mat_elash := StandardMaterial3D.new()
		mat_elash.transparency = StandardMaterial3D.TRANSPARENCY_ALPHA
		mat_elash.cull_mode = StandardMaterial3D.CULL_DISABLED
		mat_elash.shading_mode = StandardMaterial3D.SHADING_MODE_UNSHADED
		mat_elash.albedo_texture = tex_elash
		mat_elash.albedo_color = Color(1, 1, 1, 1)
		face_mesh.set_surface_override_material(3, mat_elash)

		# Slot 4: FaceBrow (清秀淡紫黛眉)
		var mat_brow := StandardMaterial3D.new()
		mat_brow.transparency = StandardMaterial3D.TRANSPARENCY_ALPHA
		mat_brow.cull_mode = StandardMaterial3D.CULL_DISABLED
		mat_brow.shading_mode = StandardMaterial3D.SHADING_MODE_UNSHADED
		mat_brow.albedo_texture = tex_brow
		face_mesh.set_surface_override_material(4, mat_brow)

		# Slot 5: EyeIris (星芒天蓝渐变二次元眼眸)
		var mat_iris := StandardMaterial3D.new()
		mat_iris.shading_mode = StandardMaterial3D.SHADING_MODE_UNSHADED
		mat_iris.albedo_texture = tex_iris
		face_mesh.set_surface_override_material(5, mat_iris)

		# Slot 6: EyeHighlight (纯净星芒晶莹高光)
		var mat_hl := StandardMaterial3D.new()
		mat_hl.transparency = StandardMaterial3D.TRANSPARENCY_ALPHA
		mat_hl.cull_mode = StandardMaterial3D.CULL_DISABLED
		mat_hl.shading_mode = StandardMaterial3D.SHADING_MODE_UNSHADED
		mat_hl.albedo_texture = tex_hl
		face_mesh.set_surface_override_material(6, mat_hl)

		# Slot 7: Face_00 (冷白通透皮肤 + 淡粉腮红 + 静谧小嘴 + 精致小鼻)
		var mat_face_skin := ShaderMaterial.new()
		mat_face_skin.shader = SHADER_FACE
		mat_face_skin.set_shader_parameter("skin_color", Color(1.0, 0.98, 0.97, 1.0))
		mat_face_skin.set_shader_parameter("face_shadow_tint", Color(0.92, 0.89, 0.95, 1.0))
		mat_face_skin.set_shader_parameter("shadow_threshold", 0.45)
		mat_face_skin.set_shader_parameter("shadow_softness", 0.03)
		mat_face_skin.set_shader_parameter("face_texture", tex_face)
		mat_face_skin.next_pass = _create_outline_pass(Color(0.35, 0.28, 0.35, 1.0), 0.0016)
		face_mesh.set_surface_override_material(7, mat_face_skin)

	# 3. 身体与服装
	if body_mesh:
		# 身体白皙皮肤与白袜 (Surface 0, 附带柔和轮廓墨线以防纯白过曝)
		var mat_body_skin = _create_toon_mat(tex_body, Color(1.0, 1.0, 1.0), true, Color(0.35, 0.28, 0.35, 1.0), 0.0, false, false)
		mat_body_skin.set_shader_parameter("shadow_tint", Color(0.88, 0.84, 0.90, 1.0))
		body_mesh.set_surface_override_material(0, mat_body_skin)
		
		# 服装：象牙白风琴褶薄衫 + 宽腰封 + 水蓝花藤刺绣层叠裙 (Surface 1)
		var mat_clothes = _create_toon_mat(tex_clothes, Color(1.0, 1.0, 1.0), true, Color(0.24, 0.26, 0.36), 0.0, true, true, tex_clothes_nml, 0.8)
		body_mesh.set_surface_override_material(1, mat_clothes)
		
		# 鞋履：白色玛丽珍圆头搭扣鞋 (Surface 2)
		var mat_shoes = _create_toon_mat(tex_shoes, Color(1.0, 1.0, 1.0), true, Color(0.26, 0.28, 0.36), 0.0, true, false)
		body_mesh.set_surface_override_material(2, mat_shoes)
		
		# 脑后发顶：珍珠银白 (Surface 3)
		var mat_back_hair = _create_hair_mat(tex_hair_back)
		body_mesh.set_surface_override_material(3, mat_back_hair)

	# 4. 头发材质 (及腰波浪银发 + 水蓝缎带与双侧花饰，双面着色)
	if hair_mesh:
		hair_mesh.set_surface_override_material(0, _create_hair_mat(tex_hair1))
		hair_mesh.set_surface_override_material(1, _create_hair_mat(tex_hair3))
	print("Finished _setup_materials!")

func _setup_pose() -> void:
	if not skeleton:
		return
	
	# 姿态：优雅文静的二次元自然 A-pose (完美还原 2D turnaround 仪态)
	var left_arm: int = skeleton.find_bone("J_Bip_L_UpperArm")
	var right_arm: int = skeleton.find_bone("J_Bip_R_UpperArm")
	var left_forearm: int = skeleton.find_bone("J_Bip_L_LowerArm")
	var right_forearm: int = skeleton.find_bone("J_Bip_R_LowerArm")
	var left_hand: int = skeleton.find_bone("J_Bip_L_Hand")
	var right_hand: int = skeleton.find_bone("J_Bip_R_Hand")
	var head: int = skeleton.find_bone("J_Bip_C_Head")
	var spine: int = skeleton.find_bone("J_Bip_C_Spine")
	
	# 左臂自然下摆 36 度 A-pose
	if left_arm != -1:
		var q_arm := Quaternion.from_euler(Vector3(deg_to_rad(3.0), deg_to_rad(-6.0), deg_to_rad(36.0)))
		skeleton.set_bone_pose_rotation(left_arm, q_arm)
	if left_forearm != -1:
		var q_fa := Quaternion.from_euler(Vector3(deg_to_rad(0.0), deg_to_rad(-4.0), deg_to_rad(6.0)))
		skeleton.set_bone_pose_rotation(left_forearm, q_fa)
	if left_hand != -1:
		var q_hand := Quaternion.from_euler(Vector3(deg_to_rad(0.0), deg_to_rad(-2.0), deg_to_rad(4.0)))
		skeleton.set_bone_pose_rotation(left_hand, q_hand)
		
	# 右臂自然下摆 -36 度 A-pose
	if right_arm != -1:
		var q_arm_r := Quaternion.from_euler(Vector3(deg_to_rad(-3.0), deg_to_rad(6.0), deg_to_rad(-36.0)))
		skeleton.set_bone_pose_rotation(right_arm, q_arm_r)
	if right_forearm != -1:
		var q_fa_r := Quaternion.from_euler(Vector3(deg_to_rad(0.0), deg_to_rad(4.0), deg_to_rad(-6.0)))
		skeleton.set_bone_pose_rotation(right_forearm, q_fa_r)
	if right_hand != -1:
		var q_hand_r := Quaternion.from_euler(Vector3(deg_to_rad(0.0), deg_to_rad(2.0), deg_to_rad(-4.0)))
		skeleton.set_bone_pose_rotation(right_hand, q_hand_r)
		
	# 头部微偏与优雅体态
	if head != -1:
		var q_head := Quaternion.from_euler(Vector3(deg_to_rad(-1.0), deg_to_rad(-1.5), deg_to_rad(1.0)))
		skeleton.set_bone_pose_rotation(head, q_head)
	if spine != -1:
		var q_spine := Quaternion.from_euler(Vector3(deg_to_rad(-1.0), deg_to_rad(0.0), deg_to_rad(0.0)))
		skeleton.set_bone_pose_rotation(spine, q_spine)
