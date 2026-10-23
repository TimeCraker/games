shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

// 地面 PBR 着色器：Albedo/Normal/Roughness/AO + 世界坐标 XZ 平铺
// （GLB 地面 UV 为退化线性条，必须走 use_world_uv 投影）。
// 光照完全交给引擎的标准 PBR（太阳、环境光、GI、反射），不写自定义 light()，
// 这样换任何 LightingPreset 地面都会正确响应。
// edge_stripe_*：世界 x 驱动的路缘 0.2m 白实线；crosswalk_*：世界 z 驱动的斑马线。

group_uniforms TextureMaps;
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D roughness_texture : hint_default_black, filter_linear_mipmap, repeat_enable;
uniform sampler2D ao_texture : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform bool use_world_uv = false;
uniform vec2 world_uv_period = vec2(2.5, 2.5);   // 一张贴图覆盖的世界尺寸（米）
uniform vec2 uv_scale = vec2(1.0, 1.0);
uniform vec2 uv_offset = vec2(0.0, 0.0);
uniform float normal_depth : hint_range(0.0, 3.0, 0.05) = 1.0;
uniform float albedo_gain : hint_range(0.0, 2.0, 0.01) = 1.0;
uniform float roughness_gain : hint_range(0.0, 2.0, 0.05) = 1.0;

group_uniforms EdgeStripe;
uniform sampler2D edge_stripe_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform float edge_stripe_line_width : hint_range(0.0, 1.0, 0.01) = 0.0;   // 0 = 关闭
uniform float edge_stripe_center = 0.0;        // 路面中心世界 x
uniform float edge_stripe_half_width = 4.0;    // 路面半宽（米）
uniform float edge_stripe_world_period = 0.8;  // 贴花纵向世界周期
uniform float edge_stripe_roughness : hint_range(0.0, 1.0, 0.01) = 0.55;
uniform float edge_stripe_feather : hint_range(0.001, 0.2, 0.001) = 0.03;

group_uniforms Crosswalk;
uniform float crosswalk_center_z = 13.5;       // 斑马线中心世界 z
uniform float crosswalk_depth = 2.6;           // 斑马线纵深（米）
uniform float crosswalk_span_half = 3.6;       // 横向半宽（米）
uniform float crosswalk_stripe_w = 0.45;       // 单条白条宽度（米）
uniform float crosswalk_gap = 0.45;            // 条间空隙（米）
uniform float crosswalk_roughness : hint_range(0.0, 1.0, 0.01) = 0.55;
uniform float crosswalk_feather : hint_range(0.001, 0.2, 0.001) = 0.025;

varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 uv;
	if (use_world_uv) {
		uv = world_pos.xz / world_uv_period + uv_offset;
	} else {
		uv = UV * uv_scale + uv_offset;
	}
	ALBEDO = texture(albedo_texture, uv).rgb * albedo_gain;
	NORMAL_MAP = texture(normal_texture, uv).xyz;
	NORMAL_MAP_DEPTH = normal_depth;
	float rough = texture(roughness_texture, uv).r * roughness_gain;
	AO = texture(ao_texture, uv).r;
	AO_LIGHT_AFFECT = 0.5;

	if (edge_stripe_line_width > 0.0) {
		float dx = abs(world_pos.x - edge_stripe_center);
		float d_edge = edge_stripe_half_width - dx;
		float m = 1.0 - smoothstep(edge_stripe_line_width - edge_stripe_feather,
				edge_stripe_line_width + edge_stripe_feather, d_edge);
		if (m > 0.001) {
			float t = clamp(d_edge / edge_stripe_line_width, 0.0, 1.0);
			float sv = fract(world_pos.z / edge_stripe_world_period);
			vec4 stripe_col = texture(edge_stripe_texture, vec2(t, sv));
			float w = m * stripe_col.a;
			ALBEDO = mix(ALBEDO, stripe_col.rgb, w);
			rough = mix(rough, edge_stripe_roughness, w);
		}
	}

	float dz = abs(world_pos.z - crosswalk_center_z);
	float in_depth = 1.0 - smoothstep(crosswalk_depth * 0.5 - crosswalk_feather,
			crosswalk_depth * 0.5 + crosswalk_feather, dz);
	float in_span = 1.0 - smoothstep(crosswalk_span_half - crosswalk_feather,
			crosswalk_span_half + crosswalk_feather, abs(world_pos.x));
	if (in_depth * in_span > 0.001) {
		float period = crosswalk_stripe_w + crosswalk_gap;
		float stripe = abs(fract(world_pos.x / period) - 0.5) * 2.0;
		float m = (1.0 - smoothstep(crosswalk_stripe_w / period - crosswalk_feather / period * 4.0,
				crosswalk_stripe_w / period + crosswalk_feather / period * 4.0, stripe))
				* in_depth * in_span;
		if (m > 0.001) {
			float wear = 0.90 + 0.10 * sin(world_pos.z * 2.1 + world_pos.x * 0.7);
			float w = m * wear;
			ALBEDO = mix(ALBEDO, vec3(0.78, 0.80, 0.82), w);
			rough = mix(rough, crosswalk_roughness, w);
		}
	}
	ROUGHNESS = clamp(rough, 0.0, 1.0);
	SPECULAR = 0.5;
}
