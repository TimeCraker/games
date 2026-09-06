extends StaticBody3D
## AsterNova - NPR setup for the dual vending machine prop prefab.
## Binds the embedded 4K Tripo albedo atlas into toon_prop.gdshader with
## showcase-window emission (bright texels glow softly for the cyber-anime
## night street feel), and chains outline.gdshader as next_pass.

const SHADER_TOON := preload("res://shaders/toon_prop.gdshader")
const SHADER_OUTLINE := preload("res://shaders/outline.gdshader")
const ALBEDO_FALLBACK := "res://models/environment/vending_machine_dual_4k_albedo.jpg"

const OUTLINE_COLOR := Color(0.22, 0.25, 0.34, 1.0)
const OUTLINE_THICKNESS := 0.0028
const SHADOW_TINT := Color(0.80, 0.82, 0.92, 1.0)
const RAMP_THRESHOLD := 0.52
const RAMP_SMOOTHNESS := 0.05


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
		var albedo_tex: Texture2D = null
		if src is BaseMaterial3D:
			albedo_tex = src.albedo_texture
		elif src is ShaderMaterial:
			albedo_tex = src.get_shader_parameter("albedo_texture")
		if albedo_tex == null:
			albedo_tex = load(ALBEDO_FALLBACK)
		var mat := ShaderMaterial.new()
		mat.render_priority = 0
		mat.shader = SHADER_TOON
		mat.set_shader_parameter("albedo_color", Color(1, 1, 1, 1))
		mat.set_shader_parameter("albedo_texture", albedo_tex)
		mat.set_shader_parameter("desaturation", 0.0)
		mat.set_shader_parameter("use_alpha_scissor", false)
		# 道具用更硬的明暗交界与浅冷调阴影，贴合金属柜体的二次元体积感
		mat.set_shader_parameter("shadow_tint", SHADOW_TINT)
		mat.set_shader_parameter("ramp_threshold", RAMP_THRESHOLD)
		mat.set_shader_parameter("ramp_smoothness", RAMP_SMOOTHNESS)
		mat.set_shader_parameter("shadow_strength", 0.38)
		mat.set_shader_parameter("enable_rim", true)
		mat.set_shader_parameter("rim_color", Color(0.85, 0.92, 1.0, 1.0))
		mat.set_shader_parameter("rim_threshold", 0.70)
		mat.set_shader_parameter("rim_smoothness", 0.05)
		mat.set_shader_parameter("rim_spread", 2.0)
		mat.set_shader_parameter("specular_color", Color(0.95, 0.97, 1.0, 1.0))
		mat.set_shader_parameter("specular_size", 0.08)
		mat.set_shader_parameter("specular_smoothness", 0.02)
		# 橱窗自发光微光：亮部贴图（窗柜、数屏、海报）柔和溢出
		mat.set_shader_parameter("enable_emission", true)
		mat.set_shader_parameter("emission_color", Color(1, 1, 1, 1))
		mat.set_shader_parameter("emission_energy", 0.40)
		mat.set_shader_parameter("emission_min_luminance", 0.70)
		mat.set_shader_parameter("emission_mask_softness", 0.18)
		# 深灰蓝 next_pass 描边
		var outline := ShaderMaterial.new()
		outline.render_priority = 1
		outline.shader = SHADER_OUTLINE
		outline.set_shader_parameter("outline_color", OUTLINE_COLOR)
		outline.set_shader_parameter("outline_thickness", OUTLINE_THICKNESS)
		outline.set_shader_parameter("distance_scaling", true)
		mat.next_pass = outline
		mi.set_surface_override_material(i, mat)
	print("[vending_npr] %s: %d surface(s) -> toon_prop+emission+outline" % [
		mi.name, mi.mesh.get_surface_count()])
