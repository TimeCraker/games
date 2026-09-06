shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

// Asternova 地面 NPR PBR 着色器 (第四执行组 Ground Pavement Pipeline)。
// 支持 Albedo/Normal(可调深度)/Roughness/AO 与独立 UV 平铺缩放；
// 特色 sky_reflection_energy：按菲涅尔与朝向混入天光色的微泛光，
// 参照 anime_victorian_dna_01 的清透反光，杜绝大面积死灰；
// 能量上限 ≤1.0，远低于 glow_hdr_threshold=1.6 防穿帮红线，地面永不呈现自发光灯泡。
// edge_stripe_* 参数组：把 asphalt_white_stripe.png 的白实线映射到路缘两侧
// （坡道专用，广场材质保持 zone=0 关闭）。

// --- 贴图与平铺 ---
group_uniforms TextureMaps;
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D roughness_texture : hint_default_black, filter_linear_mipmap, repeat_enable;
uniform sampler2D ao_texture : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec2 uv_scale = vec2(1.0, 1.0);
uniform vec2 uv_offset = vec2(0.0, 0.0);
uniform float normal_depth : hint_range(0.0, 3.0, 0.05) = 1.0;
uniform float roughness_gain : hint_range(0.0, 2.0, 0.05) = 1.0;

// --- 柔和赛璐璐 (地面用宽坡度, 不出硬色阶带) ---
group_uniforms ToonShading;
uniform vec4 shadow_tint : source_color = vec4(0.74, 0.80, 0.92, 1.0);
uniform float ramp_threshold : hint_range(0.0, 1.0, 0.01) = 0.40;
uniform float ramp_smoothness : hint_range(0.02, 0.6, 0.01) = 0.28;
uniform float shadow_strength : hint_range(0.0, 1.0, 0.05) = 0.42;

// --- 天光清透反光 ---
group_uniforms SkyReflection;
uniform vec4 sky_tint : source_color = vec4(0.70, 0.84, 1.0, 1.0);
uniform float sky_reflection_energy : hint_range(0.0, 1.0, 0.01) = 0.16;
uniform float sky_fresnel_power : hint_range(0.5, 8.0, 0.1) = 3.0;

// --- 车道边缘白实线 (坡道) ---
group_uniforms EdgeStripe;
uniform sampler2D edge_stripe_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform float edge_stripe_zone : hint_range(0.0, 0.2, 0.002) = 0.0;
uniform float edge_stripe_u0 : hint_range(0.0, 1.0) = 0.151;
uniform float edge_stripe_span : hint_range(0.0, 1.0) = 0.309;
uniform float edge_stripe_v_period : hint_range(0.1, 8.0, 0.01) = 1.332;
uniform float edge_stripe_roughness : hint_range(0.0, 1.0, 0.01) = 0.58;
uniform float edge_stripe_feather : hint_range(0.001, 0.05, 0.001) = 0.005;

void fragment() {
	vec2 uv = UV * uv_scale + uv_offset;
	ALBEDO = texture(albedo_texture, uv).rgb;
	NORMAL_MAP = texture(normal_texture, uv).xyz;
	NORMAL_MAP_DEPTH = normal_depth;
	float rough = texture(roughness_texture, uv).r * roughness_gain;
	AO = texture(ao_texture, uv).r;
	AO_LIGHT_AFFECT = 0.85;

	// 路缘白实线: 左右两侧镜像采样条带, 白漆区压低粗糙度 (微光反弹)
	if (edge_stripe_zone > 0.0) {
		float d_edge = min(UV.x, 1.0 - UV.x);
		float m = 1.0 - smoothstep(edge_stripe_zone - edge_stripe_feather,
				edge_stripe_zone + edge_stripe_feather, d_edge);
		if (m > 0.001) {
			float t = clamp(d_edge / edge_stripe_zone, 0.0, 1.0);
			bool right_side = UV.x > 0.5;
			float su = mix(edge_stripe_u0, edge_stripe_u0 + edge_stripe_span, t);
			if (right_side) {
				su = mix(1.0 - edge_stripe_u0 - edge_stripe_span,
						1.0 - edge_stripe_u0, t);
			}
			float sv = fract(uv.y / edge_stripe_v_period);
			vec3 stripe_col = texture(edge_stripe_texture, vec2(su, sv)).rgb;
			ALBEDO = mix(ALBEDO, stripe_col, m);
			rough = mix(rough, edge_stripe_roughness, m);
		}
	}
	ROUGHNESS = clamp(rough, 0.0, 1.0);
	SPECULAR = 0.5;

	// 天光微泛光: 菲涅尔 + 朝天加权, 按粗糙度衰减 (愈糙愈弱), 上限远低于泛光阈值
	float n_dot_v = clamp(dot(normalize(NORMAL), VIEW), 0.0, 1.0);
	float fresnel = pow(1.0 - n_dot_v, sky_fresnel_power);
	float up_factor = clamp(NORMAL.y * 0.5 + 0.5, 0.0, 1.0);
	float sky_mask = (0.25 + 0.75 * fresnel) * up_factor * (1.0 - ROUGHNESS * 0.55);
	EMISSION += sky_tint.rgb * sky_mask * sky_reflection_energy;
}

void light() {
	// 1. 半兰伯特 + 宽平滑阶梯: 地面保持通透, 阴影面留冷色微光不死黑
	float ndl = dot(NORMAL, LIGHT);
	float half_lambert = clamp(ndl * 0.5 + 0.5, 0.0, 1.0);
	float w = ramp_smoothness * 0.5;
	float lit = smoothstep(ramp_threshold - w, ramp_threshold + w,
			half_lambert * ATTENUATION);
	vec3 tint = mix(shadow_tint.rgb * (1.0 - shadow_strength), vec3(1.0), lit);
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * tint * ATTENUATION;

	// 2. 粗糙度驱动的柔和镜面: 白漆/光滑区微光, 粗糙沥青几乎无高光
	vec3 h = normalize(VIEW + LIGHT);
	float nh = clamp(dot(NORMAL, h), 0.0, 1.0);
	float spec = pow(nh, mix(90.0, 10.0, clamp(ROUGHNESS, 0.0, 1.0)))
			* (1.0 - ROUGHNESS);
	SPECULAR_LIGHT += vec3(0.90, 0.95, 1.0) * LIGHT_COLOR * spec * 0.35 * lit;
}
