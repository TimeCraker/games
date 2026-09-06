extends Node
## AsterNova - Ground PBR NPR setup (第四执行组 Ground Pavement Pipeline).
## 对 modern_japan_neighborhood.glb 中现存的广场/坡道地面网格运行时覆盖材质：
## 米白防滑方砖 + 暖姜黄盲道 + 深灰沥青(坡道带白实线路缘)，严禁重新建模。
## 贴图来自 process_ground_pbr.py 产出的 2K PBR 套件。
## GLB 地面网格顶面 UV 为退化线性条（只采样贴图一行像素），因此全部启用
## 着色器的世界坐标 XZ 投影（use_world_uv），world_uv_period = 贴图世界尺寸(米)。

const SHADER_GROUND := preload("res://shaders/toon_ground_pbr.gdshader")
const TEX_DIR := "res://art/textures/ground/"

# 目标网格名 -> [贴图组, world_uv_period(米), uv_offset, 启用白实线路缘]
const ZONE_MAP := {
	"Plaza_Sidewalk_West": ["tiles", Vector2(2.4, 2.4), Vector2(0.0, 0.0), false],
	"Ramp_Sidewalk_West": ["tiles", Vector2(2.4, 2.4), Vector2(0.0, 0.0), false],
	"Plaza_Tactile_Line": ["tactile", Vector2(0.9, 0.9), Vector2(0.167, 0.0), false],
	"Plaza_Asphalt_Road": ["asphalt", Vector2(2.5, 2.5), Vector2(0.0, 0.0), false],
	"Ramp_Asphalt_Road": ["asphalt", Vector2(2.5, 2.5), Vector2(0.0, 0.0), true],
}

var _textures: Dictionary = {}


func _ready() -> void:
	_load_textures()
	# 遍历父级（场景根），而非自身子树：本节点只作为独立挂载的驱动器
	_apply(get_parent())


func _load_textures() -> void:
	for group in ["tiles", "tactile", "asphalt"]:
		_textures[group] = {
			"albedo": load(TEX_DIR + "ground_%s_albedo.png" % group),
			"normal": load(TEX_DIR + "ground_%s_normal.png" % group),
			"roughness": load(TEX_DIR + "ground_%s_roughness.png" % group),
		}
	_textures["tiles"]["ao"] = load(TEX_DIR + "ground_tiles_ao.png")
	_textures["stripe"] = load(TEX_DIR + "asphalt_white_stripe.png")


func _apply(root: Node) -> void:
	for child in root.get_children():
		if child is MeshInstance3D:
			for zone_name in ZONE_MAP:
				# GLB 节点在 Godot 导入后名字保持，模糊匹配防实例化改名
				if String(child.name).findn(zone_name) >= 0:
					_setup_mesh(child, zone_name)
					break
		_apply(child)


func _setup_mesh(mi: MeshInstance3D, zone_name: String) -> void:
	var cfg: Array = ZONE_MAP[zone_name]
	var group: String = cfg[0]
	var period: Vector2 = cfg[1]
	var uv_off: Vector2 = cfg[2]
	var edge_stripe: bool = cfg[3]
	var tex: Dictionary = _textures[group]
	for i in mi.mesh.get_surface_count():
		var mat := ShaderMaterial.new()
		mat.shader = SHADER_GROUND
		mat.set_shader_parameter("albedo_texture", tex["albedo"])
		mat.set_shader_parameter("normal_texture", tex["normal"])
		mat.set_shader_parameter("roughness_texture", tex["roughness"])
		mat.set_shader_parameter("ao_texture", tex.get("ao"))
		mat.set_shader_parameter("use_world_uv", true)
		mat.set_shader_parameter("world_uv_period", period)
		mat.set_shader_parameter("uv_offset", uv_off)
		mat.set_shader_parameter("normal_depth", 0.5 if group == "asphalt" else 0.9)
		if edge_stripe:
			# 坡道路面世界 x ∈ [-4, 4]：两侧 0.2m 白实线，白漆 rough 0.58
			mat.set_shader_parameter("edge_stripe_texture", _textures["stripe"])
			mat.set_shader_parameter("edge_stripe_line_width", 0.2)
			mat.set_shader_parameter("edge_stripe_center", 0.0)
			mat.set_shader_parameter("edge_stripe_half_width", 4.0)
			mat.set_shader_parameter("edge_stripe_u0", 0.151)
			mat.set_shader_parameter("edge_stripe_span", 0.309)
			mat.set_shader_parameter("edge_stripe_world_period", 3.33)
			mat.set_shader_parameter("edge_stripe_roughness", 0.58)
			mat.set_shader_parameter("edge_stripe_feather", 0.03)
		mi.set_surface_override_material(i, mat)
	print("[ground_npr] %s -> %s (world_uv_period=%s, offset=%s, edge_stripe=%s)" % [
			zone_name, group, period, uv_off, edge_stripe])
