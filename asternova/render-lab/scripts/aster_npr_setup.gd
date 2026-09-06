extends Node3D
## Asternova - NPR setup for the assembled Tripo Aster hero (aster_assembled.glb).
## Binds the embedded 4K BaseColor atlas into toon_character.gdshader with the
## STYLE.md M1 celadro palette, and chains outline.gdshader as next_pass.

const SHADER_TOON := preload("res://shaders/toon_character.gdshader")
const SHADER_OUTLINE := preload("res://shaders/outline.gdshader")

const OUTLINE_COLOR := Color(0.24, 0.26, 0.36, 1.0)
const OUTLINE_THICKNESS := 0.0022
const SHADOW_TINT := Color(0.82, 0.84, 0.92, 1.0)
const RAMP_THRESHOLD := 0.48
const RAMP_SMOOTHNESS := 0.04
const RIM_COLOR := Color(0.85, 0.92, 1.0, 1.0)

const KATANA_ATLAS_FALLBACK := "res://models/aster/katana_basecolor.png"

var _mesh_count := 0
var _surface_count := 0


func _ready() -> void:
	_apply_npr(self)


func _apply_npr(root: Node) -> void:
	for child in root.get_children():
		if child is MeshInstance3D:
			_setup_mesh(child)
		_apply_npr(child)


func _setup_mesh(mi: MeshInstance3D) -> void:
	_mesh_count += 1
	for i in mi.mesh.get_surface_count():
		var src := mi.get_active_material(i)
		var albedo_tex: Texture2D = null
		if src is BaseMaterial3D:
			albedo_tex = src.albedo_texture
		elif src is ShaderMaterial:
			albedo_tex = src.get_shader_parameter("albedo_texture")
		# Godot can drop the shared atlas on some katana surfaces -> black render
		if albedo_tex == null and mi.name.begins_with("Katana"):
			albedo_tex = load(KATANA_ATLAS_FALLBACK)
		var mat := ShaderMaterial.new()
		mat.render_priority = 0
		mat.shader = SHADER_TOON
		mat.set_shader_parameter("albedo_color", Color(1, 1, 1, 1))
		mat.set_shader_parameter("albedo_texture", albedo_tex)
		mat.set_shader_parameter("desaturation", 0.0)
		mat.set_shader_parameter("use_alpha_scissor", false)
		# 二次元日系柔和冷紫阴影阶梯 (STYLE.md M1 定稿)
		mat.set_shader_parameter("shadow_tint", SHADOW_TINT)
		mat.set_shader_parameter("ramp_threshold", RAMP_THRESHOLD)
		mat.set_shader_parameter("ramp_smoothness", RAMP_SMOOTHNESS)
		mat.set_shader_parameter("shadow_strength", 0.45)
		# 受光边缘轮廓光
		mat.set_shader_parameter("enable_rim", true)
		mat.set_shader_parameter("rim_color", RIM_COLOR)
		mat.set_shader_parameter("rim_threshold", 0.65)
		mat.set_shader_parameter("rim_smoothness", 0.04)
		mat.set_shader_parameter("rim_spread", 2.2)
		mat.set_shader_parameter("specular_color", Color(0.95, 0.97, 1.0, 1.0))
		mat.set_shader_parameter("specular_size", 0.05)
		mat.set_shader_parameter("specular_smoothness", 0.015)
		# 深灰蓝 next_pass 描边
		var outline := ShaderMaterial.new()
		outline.render_priority = 1
		outline.shader = SHADER_OUTLINE
		outline.set_shader_parameter("outline_color", OUTLINE_COLOR)
		outline.set_shader_parameter("outline_thickness", OUTLINE_THICKNESS)
		outline.set_shader_parameter("distance_scaling", true)
		mat.next_pass = outline
		mi.set_surface_override_material(i, mat)
		_surface_count += 1
	print("[aster_npr] %s: %d surfaces -> toon+outline" % [mi.name, mi.mesh.get_surface_count()])
