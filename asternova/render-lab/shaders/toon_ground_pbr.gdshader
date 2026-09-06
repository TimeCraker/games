shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

// Asternova 地面 NPR PBR 着色器 (第四执行组 Ground Pavement Pipeline)。
// 支持 Albedo/Normal(可调深度)/Roughness/AO 与独立 UV 平铺缩放；
// use_world_uv：GLB 地面网格顶面 UV 为退化线性条(只采样贴图一行)，
// 此时改用世界坐标 XZ 投影 + world_uv_period(米/张) 平铺，彻底摆脱网格 UV 质量；
// 特色 sky_reflection_energy：按菲涅尔与朝向混入天光色的微泛光，
// 参照 anime_victorian_dna_01 的清透反光，杜绝大面积死灰；
// 能量上限 ≤1.0，远低于 glow_hdr_threshold=1.6 防穿帮红线，地面永不呈现自发光灯泡。
// edge_stripe_* 参数组：世界 x 坐标驱动的路缘白实线（坡道专用，广场保持 line_width=0 关闭）。

// --- 贴图与平铺 ---
group_uniforms TextureMaps;
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D roughness_texture : hint_default_black, filter_linear_mipmap, repeat_enable;
uniform sampler2D ao_texture : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform bool use_world_uv = false;
uniform vec2 world_uv_period = vec2(2.5, 2.5);   // 一张贴图覆盖的世界尺寸 (米)
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

// --- 车道边缘白实线 (世界坐标驱动, 坡道) ---
group_uniforms EdgeStripe;
uniform sampler2D edge_stripe_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform float edge_stripe_line_width : hint_range(0.0, 1.0, 0.01) = 0.0;   // 0 = 关闭
uniform float edge_stripe_center = 0.0;        // 路面中心世界 x
uniform float edge_stripe_half_width = 4.0;    // 路面半宽 (米)
uniform float edge_stripe_u0 : hint_range(0.0, 1.0) = 0.151;
uniform float edge_stripe_span : hint_range(0.0, 1.0) = 0.309;
uniform float edge_stripe_world_period = 3.33; // 条带纹理纵向世界周期 (米)
uniform float edge_stripe_roughness : hint_range(0.0, 1.0, 0.01) = 0.58;
uniform float edge_stripe_feather : hint_range(0.001, 0.2, 0.001) = 0.03;

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
	ALBEDO = texture(albedo_texture, uv).rgb;
	NORMAL_MAP = texture(normal_texture, uv).xyz;
	NORMAL_MAP_DEPTH = normal_depth;
	float rough = texture(roughness_texture, uv).r * roughness_gain;
	AO = texture(ao_texture, uv).r;
	AO_LIGHT_AFFECT = 0.85;

	// 路缘白实线: 世界 x 距路缘 < line_width 处镜像采样条带, 白漆压低粗糙度
	if (edge_stripe_line_width > 0.0) {
		float dx = abs(world_pos.x - edge_stripe_center);
		float d_edge = edge_stripe_half_width - dx;     // 距路缘的横向距离
		float m = 1.0 - smoothstep(edge_stripe_line_width - edge_stripe_feather,
				edge_stripe_line_width + edge_stripe_feather, d_edge);
		if (m > 0.001) {
			float t = clamp(d_edge / edge_stripe_line_width, 0.0, 1.0);
			bool right_side = world_pos.x > edge_stripe_center;
			float su = mix(edge_stripe_u0, edge_stripe_u0 + edge_stripe_span, t);
			if (right_side) {
				// 同一漆区反向扫描 (漆区偏离条带中心, 不可按 0.5 镜像)
				su = mix(edge_stripe_u0 + edge_stripe_span, edge_stripe_u0, t);
			}
			float sv = fract(world_pos.z / edge_stripe_world_period);
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

	// 2. 粗糙度驱动的柔和镜面: (1-rough)^2 强衰减, 粗糙沥青零闪砂, 白漆留柔光
	vec3 h = normalize(VIEW + LIGHT);
	float nh = clamp(dot(NORMAL, h), 0.0, 1.0);
	float gloss = pow(clamp(1.0 - ROUGHNESS, 0.0, 1.0), 2.0);
	float spec = pow(nh, mix(90.0, 10.0, clamp(ROUGHNESS, 0.0, 1.0))) * gloss;
	SPECULAR_LIGHT += vec3(0.90, 0.95, 1.0) * LIGHT_COLOR * spec * 0.3 * lit;
}
