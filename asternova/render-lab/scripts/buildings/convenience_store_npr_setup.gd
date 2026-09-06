extends StaticBody3D
## AsterNova - NPR setup for the corner convenience store landmark prefab.
## Walls/sign bind the embedded 8K Tripo albedo atlas into toon_prop.gdshader
## with warm-white luminance-masked emission (the 24 コンビニ lightbox band and
## bright storefront content glow softly for the anime street feel) and chain
## outline.gdshader as next_pass. Surfaces whose material is named
## *glass* (mat_convenience_glass) get the see-through glass_facade.gdshader
## with alpha transparency + fresnel sheen so the warm interior stays visible
## from the street.

const SHADER_TOON := preload("res://shaders/toon_prop.gdshader")
const SHADER_OUTLINE := preload("res://shaders/outline.gdshader")
const SHADER_GLASS := preload("res://shaders/glass_facade.gdshader")

const OUTLINE_COLOR := Color(0.22, 0.25, 0.34, 1.0)
const OUTLINE_THICKNESS := 0.0022
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
		var mat_name := ""
		var albedo_tex: Texture2D = null
		if src is BaseMaterial3D:
			mat_name = src.resource_name
			albedo_tex = src.albedo_texture
		elif src is ShaderMaterial:
			mat_name = src.resource_name
			albedo_tex = src.get_shader_parameter("albedo_texture")
		if mat_name.containsn("glass"):
			var glass := ShaderMaterial.new()
			glass.render_priority = 0
			glass.shader = SHADER_GLASS
			glass.set_shader_parameter("albedo_color", Color(0.85, 0.95, 1.0, 0.22))
			glass.set_shader_parameter("metallic", 0.35)
			glass.set_shader_parameter("roughness", 0.06)
			glass.set_shader_parameter("fresnel_power", 3.0)
			glass.set_shader_parameter("fresnel_boost", 0.55)
			glass.set_shader_parameter("reflection_tint", Color(0.9, 0.96, 1.0))
			glass.set_shader_parameter("reflection_glow", 0.25)
			mi.set_surface_override_material(i, glass)
			continue
		var mat := ShaderMaterial.new()
		mat.render_priority = 0
		mat.shader = SHADER_TOON
		mat.set_shader_parameter("albedo_color", Color(1, 1, 1, 1))
		mat.set_shader_parameter("albedo_texture", albedo_tex)
		mat.set_shader_parameter("desaturation", 0.0)
		mat.set_shader_parameter("use_alpha_scissor", false)
		# 建筑外墙：明暗交界偏硬、浅冷调阴影，维持二次元硬表面体积感
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
		# 门头灯箱浅暖白微光：亮部贴图（24 コンビニ 灯箱、白条纹）柔和溢出，
		# 阈值抬高避免白色外饰（回收箱/机身）一起泛光
		mat.set_shader_parameter("enable_emission", true)
		mat.set_shader_parameter("emission_color", Color(1.0, 0.93, 0.82, 1.0))
		mat.set_shader_parameter("emission_energy", 0.38)
		mat.set_shader_parameter("emission_min_luminance", 0.80)
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
	print("[store_npr] %s: %d surface(s) processed" % [mi.name, mi.mesh.get_surface_count()])
