extends StaticBody3D
## AsterNova - Street prop NPR setup (Tier 3 生活道具通用赛璐璐绑定).
## 读取 GLB 导入的 StandardMaterial3D 底色, 重绑 toon_prop.gdshader + outline
## next_pass (与贩卖机同款二次元体积感); 金属件保持冷灰高光, 无自发光。

const SHADER_TOON := preload("res://shaders/toon_prop.gdshader")
const SHADER_OUTLINE := preload("res://shaders/outline.gdshader")

const OUTLINE_COLOR := Color(0.22, 0.25, 0.34, 1.0)
const OUTLINE_THICKNESS := 0.0024
const SHADOW_TINT := Color(0.80, 0.82, 0.92, 1.0)


func _ready() -> void:
	_apply_npr(self)


func _apply_npr(root: Node) -> void:
	for child in root.get_children():
		if child is MeshInstance3D:
			_setup_mesh(child)
		_apply_npr(child)


func _setup_mesh(mi: MeshInstance3D) -> void:
	for i in mi.mesh.get_surface_count():
		var src := mi.get_active_material(i)
		# 取 GLB 命名材质底色 (Blender palette 直出), 丢失则回退中性灰
		var albedo := Color(0.72, 0.73, 0.74, 1)
		if src is BaseMaterial3D:
			albedo = (src as BaseMaterial3D).albedo_color
		var mat := ShaderMaterial.new()
		mat.render_priority = 0
		mat.shader = SHADER_TOON
		mat.set_shader_parameter("albedo_color", albedo)
		mat.set_shader_parameter("desaturation", 0.0)
		mat.set_shader_parameter("use_alpha_scissor", false)
		# 硬表面道具: 硬明暗交界 + 浅冷调阴影 + 克制边缘光
		mat.set_shader_parameter("shadow_tint", SHADOW_TINT)
		mat.set_shader_parameter("ramp_threshold", 0.52)
		mat.set_shader_parameter("ramp_smoothness", 0.05)
		mat.set_shader_parameter("shadow_strength", 0.38)
		mat.set_shader_parameter("enable_rim", true)
		mat.set_shader_parameter("rim_color", Color(0.85, 0.92, 1.0, 1.0))
		mat.set_shader_parameter("rim_threshold", 0.70)
		mat.set_shader_parameter("rim_smoothness", 0.05)
		mat.set_shader_parameter("rim_spread", 2.0)
		mat.set_shader_parameter("specular_color", Color(0.92, 0.95, 1.0, 1.0))
		mat.set_shader_parameter("specular_size", 0.07)
		mat.set_shader_parameter("specular_smoothness", 0.02)
		mat.set_shader_parameter("enable_emission", false)
		var outline := ShaderMaterial.new()
		outline.render_priority = 1
		outline.shader = SHADER_OUTLINE
		outline.set_shader_parameter("outline_color", OUTLINE_COLOR)
		outline.set_shader_parameter("outline_thickness", OUTLINE_THICKNESS)
		outline.set_shader_parameter("distance_scaling", true)
		mat.next_pass = outline
		mi.set_surface_override_material(i, mat)
