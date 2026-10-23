@tool
class_name LightingRig
extends Node3D

## 场景光照入口：一个场景放一个 LightingRig，选一个 LightingPreset。
## 自动生成太阳（DirectionalLight3D）与 WorldEnvironment；编辑器里改预设参数即时预览。
## 运行时按 F1~F8 切换 presets 列表里的预设，便于对比。

const PRACTICAL_GROUP := &"practical_light"
const BASE_ENERGY_META := &"lighting_base_energy"

@export var preset: LightingPreset:
	set(value):
		if preset and preset.changed.is_connected(apply):
			preset.changed.disconnect(apply)
		preset = value
		if preset and not preset.changed.is_connected(apply):
			preset.changed.connect(apply)
		if is_inside_tree():
			apply()

## 运行时 F1~F8 对应的预设
@export var presets: Array[LightingPreset] = []

## 阴影最远距离（米）。场景越大越要加大，但近处阴影会变糊
@export_range(20.0, 500.0, 1.0) var shadow_max_distance: float = 120.0

var sun: DirectionalLight3D
var world_environment: WorldEnvironment


func _ready() -> void:
	apply()


func _unhandled_key_input(event: InputEvent) -> void:
	if Engine.is_editor_hint() or not event.is_pressed() or event.is_echo():
		return
	var index := (event as InputEventKey).keycode - KEY_F1
	if index >= 0 and index < mini(presets.size(), 8) and presets[index]:
		preset = presets[index]
		print("[LightingRig] preset: ", preset.display_name)


func apply() -> void:
	if preset == null:
		return
	_ensure_nodes()
	_apply_sun()
	_apply_environment()
	_apply_practical_lights()


func _ensure_nodes() -> void:
	sun = get_node_or_null("Sun") as DirectionalLight3D
	if sun == null:
		sun = DirectionalLight3D.new()
		sun.name = "Sun"
		add_child(sun)
	world_environment = get_node_or_null("WorldEnvironment") as WorldEnvironment
	if world_environment == null:
		world_environment = WorldEnvironment.new()
		world_environment.name = "WorldEnvironment"
		add_child(world_environment)
	if world_environment.environment == null:
		world_environment.environment = Environment.new()


func _apply_sun() -> void:
	var p := preset
	sun.rotation_degrees = Vector3(-p.sun_elevation, p.sun_azimuth, 0.0)
	sun.light_color = p.sun_color
	sun.light_energy = p.sun_energy
	sun.light_angular_distance = p.sun_angular_size
	sun.shadow_enabled = p.sun_shadows
	sun.shadow_bias = 0.03
	sun.shadow_normal_bias = 1.0
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_blend_splits = true
	sun.directional_shadow_max_distance = shadow_max_distance
	# 太阳低于地平线时仍保留天空，但不再投射直射光
	sun.visible = p.sun_elevation > -2.0


func _apply_environment() -> void:
	var p := preset
	var env := world_environment.environment

	env.background_mode = Environment.BG_SKY
	if env.sky == null:
		env.sky = Sky.new()
	if p.sky_panorama:
		var pano := env.sky.sky_material as PanoramaSkyMaterial
		if pano == null:
			pano = PanoramaSkyMaterial.new()
			env.sky.sky_material = pano
		pano.panorama = p.sky_panorama
		pano.energy_multiplier = p.sky_energy
	else:
		var sky_mat := env.sky.sky_material as ProceduralSkyMaterial
		if sky_mat == null:
			sky_mat = ProceduralSkyMaterial.new()
			env.sky.sky_material = sky_mat
		sky_mat.sky_top_color = p.sky_top_color
		sky_mat.sky_horizon_color = p.sky_horizon_color
		sky_mat.ground_horizon_color = p.ground_horizon_color
		sky_mat.ground_bottom_color = p.ground_bottom_color
		sky_mat.sky_energy_multiplier = p.sky_energy
		sky_mat.ground_energy_multiplier = p.sky_energy
	env.sky_rotation = Vector3(0.0, deg_to_rad(p.sky_rotation), 0.0)

	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_color = p.ambient_color
	env.ambient_light_sky_contribution = p.ambient_sky_contribution
	env.ambient_light_energy = p.ambient_energy
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY

	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = p.exposure
	env.adjustment_enabled = not (is_equal_approx(p.contrast, 1.0) and is_equal_approx(p.saturation, 1.0))
	env.adjustment_contrast = p.contrast
	env.adjustment_saturation = p.saturation

	env.sdfgi_enabled = p.sdfgi_enabled
	env.sdfgi_use_occlusion = true
	env.sdfgi_energy = p.sdfgi_energy
	env.sdfgi_bounce_feedback = p.sdfgi_bounce
	env.ssil_enabled = p.ssil_enabled
	env.ssil_intensity = p.ssil_intensity

	env.ssao_enabled = p.ssao_enabled
	env.ssao_intensity = p.ssao_intensity
	env.ssao_radius = p.ssao_radius
	env.ssr_enabled = p.ssr_enabled

	env.fog_enabled = p.fog_enabled
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_light_color = p.fog_color
	env.fog_density = p.fog_density
	env.fog_aerial_perspective = p.fog_aerial_perspective
	env.fog_sun_scatter = p.fog_sun_scatter
	env.fog_sky_affect = 0.3
	env.volumetric_fog_enabled = p.volumetric_fog_enabled
	env.volumetric_fog_density = p.volumetric_fog_density
	env.volumetric_fog_albedo = p.volumetric_fog_albedo

	env.glow_enabled = p.glow_enabled
	env.glow_intensity = p.glow_intensity
	env.glow_hdr_threshold = p.glow_threshold
	env.glow_bloom = p.glow_bloom


func _apply_practical_lights() -> void:
	if not is_inside_tree():
		return
	for node in get_tree().get_nodes_in_group(PRACTICAL_GROUP):
		var light := node as Light3D
		if light == null:
			continue
		if not light.has_meta(BASE_ENERGY_META):
			light.set_meta(BASE_ENERGY_META, light.light_energy)
		light.light_energy = float(light.get_meta(BASE_ENERGY_META)) * preset.practical_light_scale
