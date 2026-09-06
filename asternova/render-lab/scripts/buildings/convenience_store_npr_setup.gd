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
const EMISSION_MASK := preload("res://models/environment/convenience_store/convenience_store_emission_mask.png")
const ALBEDO_GAME := preload("res://models/environment/convenience_store/convenience_store_albedo_game.jpg")

const OUTLINE_COLOR := Color(0.22, 0.25, 0.34, 1.0)
const OUTLINE_THICKNESS := 0.0022
const SHADOW_TINT := Color(0.80, 0.82, 0.92, 1.0)
const RAMP_THRESHOLD := 0.52
const RAMP_SMOOTHNESS := 0.05


func _ready() -> void:
	# 只装配便利店 glb 子树；吊顶/灯具等附属网格保持自带材质
	var building := get_node_or_null("Building")
	if building:
		_apply_npr(building)


func _apply_npr(root: Node) -> void:
	for child in root.get_children():
		if child is MeshInstance3D:
			_setup_mesh(child)
		_apply_npr(child)


func _setup_mesh(mi: MeshInstance3D) -> void:
	# PBR 实装面（混凝土/铝/灯箱/文字/货架/LED）保留 Blender 端材质，不做 NPR 覆盖
	if mi.name.begins_with("Sign") or mi.name.begins_with("Fittings") 			or mi.name.begins_with("LEDStrip") or mi.name.begins_with("Products_"):
		return
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
			glass.set_shader_parameter("albedo_color", Color(0.85, 0.95, 1.0, 0.12))
			glass.set_shader_parameter("metallic", 0.35)
			glass.set_shader_parameter("roughness", 0.06)
			glass.set_shader_parameter("fresnel_power", 3.0)
			glass.set_shader_parameter("fresnel_boost", 0.55)
			glass.set_shader_parameter("reflection_tint", Color(0.9, 0.96, 1.0))
			glass.set_shader_parameter("reflection_glow", 0.25)
			mi.set_surface_override_material(i, glass)
			continue
		if mat_name.begins_with("mat_pbr_"):
			# Phase 2/3 PBR 面（混凝土/铝型材/灯箱/货架/LED）：Blender 端已按
			# 终末地工业风配好 PBR 参数，保留导入材质不做 NPR 覆盖
			continue
		if mat_name.containsn("mat_prod_"):
			continue
		if mat_name.containsn("crown"):
			# 冠部/雨棚端头薄板：原图集 UV 退化呈噪点马赛克，改素色暖灰材质
			var crown := StandardMaterial3D.new()
			crown.albedo_color = Color(0.62, 0.60, 0.57, 1.0)
			crown.roughness = 0.9
			mi.set_surface_override_material(i, crown)
			continue
		var mat := ShaderMaterial.new()
		mat.render_priority = 0
		mat.shader = SHADER_TOON
		# 统一改绑店内提亮后的衍生贴图（Tripo 图集的店内墙面烘焙偏暗）
		mat.set_shader_parameter("albedo_color", Color(1, 1, 1, 1))
		mat.set_shader_parameter("albedo_texture", ALBEDO_GAME)
		mat.set_shader_parameter("desaturation", 0.0)
		mat.set_shader_parameter("use_alpha_scissor", false)
		# 建筑外墙：明暗交界偏硬、浅冷调阴影；ramp 阈值较道具下调，
		# 避免平方衰减下的店内墙面整体跌进阴影档变成靛蓝死区
		mat.set_shader_parameter("shadow_tint", SHADOW_TINT)
		mat.set_shader_parameter("ramp_threshold", 0.42)
		mat.set_shader_parameter("ramp_smoothness", RAMP_SMOOTHNESS)
		mat.set_shader_parameter("shadow_strength", 0.34)
		mat.set_shader_parameter("enable_rim", true)
		mat.set_shader_parameter("rim_color", Color(0.85, 0.92, 1.0, 1.0))
		mat.set_shader_parameter("rim_threshold", 0.70)
		mat.set_shader_parameter("rim_smoothness", 0.05)
		mat.set_shader_parameter("rim_spread", 2.0)
		mat.set_shader_parameter("specular_color", Color(0.95, 0.97, 1.0, 1.0))
		mat.set_shader_parameter("specular_size", 0.08)
		mat.set_shader_parameter("specular_smoothness", 0.02)
		# 门头灯箱浅暖白微光：烘焙 UV 几何遮罩只点亮 24 コンビニ 招牌白带，
		# 瓷砖墙/回收箱/踢脚面板零泄漏（用户硬底线：禁止亮度提取式发光）
		mat.set_shader_parameter("enable_emission", true)
		mat.set_shader_parameter("use_emission_mask", true)
		mat.set_shader_parameter("emission_mask_texture", EMISSION_MASK)
		mat.set_shader_parameter("emission_color", Color(1.0, 0.95, 0.88, 1.0))
		mat.set_shader_parameter("emission_energy", 1.2)
		mat.set_shader_parameter("emission_mask_softness", 0.2)
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
