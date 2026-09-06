shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

// Asternova 地面 NPR PBR 着色器 (第四执行组 Ground Pavement Pipeline · 纠偏版)。
// 支持 Albedo/Normal/Roughness/AO 与世界坐标 XZ 平铺 (GLB 地面 UV 为退化线性条,
// 必须走 use_world_uv 投影)。沥青的真实感由贴图颗粒 + 法线咬合 + SSAO + 反射探针
// 的正确 PBR 路径呈现: 禁止用 EMISSION 伪造天光 (路面不是自发光显示器)。
// diffuse_gain 处于正常物理区间 0.85~1.0 (Forward+ + AgX, 无需降权)。
// edge_stripe_*: 世界 x 驱动的路缘 0.2m 白实线 (贴花 RGBA, 坡道与广场共用 => 全程连贯)。
// crosswalk_*: 世界 z 驱动的横向过街斑马线 (坡道底部, 程序化条纹 + 磨损)。

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
uniform float diffuse_gain : hint_range(0.0, 2.0, 0.01) = 0.85;   // 正常物理区间下限 (纠偏令 0.85~1.0)
uniform float roughness_gain : hint_range(0.0, 2.0, 0.05) = 1.0;
uniform float ambient_fill : hint_range(0.0, 4.0, 0.05) = 1.4;   // 天光环境填充系数 (暗色沥青高, 亮色方砖低)

// --- 柔和赛璐璐 (地面用宽坡度, 不出硬色阶带) ---
group_uniforms ToonShading;
uniform vec4 shadow_tint : source_color = vec4(0.74, 0.80, 0.92, 1.0);
uniform float ramp_threshold : hint_range(0.0, 1.0, 0.01) = 0.40;
uniform float ramp_smoothness : hint_range(0.02, 0.6, 0.01) = 0.28;
uniform float shadow_strength : hint_range(0.0, 1.0, 0.05) = 0.25;   // 阴影面保持天光可读 (拒死黑)

// --- 车道边缘白实线 (世界坐标驱动, 坡道与广场共用, 全程连贯) ---
group_uniforms EdgeStripe;
uniform sampler2D edge_stripe_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform float edge_stripe_line_width : hint_range(0.0, 1.0, 0.01) = 0.0;   // 0 = 关闭
uniform float edge_stripe_center = 0.0;        // 路面中心世界 x
uniform float edge_stripe_half_width = 4.0;    // 路面半宽 (米)
uniform float edge_stripe_world_period = 0.8;  // 贴花纵向世界周期 (512:2048 = 0.2m 宽 x 0.8m 长)
uniform float edge_stripe_roughness : hint_range(0.0, 1.0, 0.01) = 0.55;   // 白漆 rough (纠偏令)
uniform float edge_stripe_feather : hint_range(0.001, 0.2, 0.001) = 0.03;

// --- 过街斑马线 (世界 z 驱动, 坡道底部横向白条) ---
group_uniforms Crosswalk;
uniform float crosswalk_center_z = 13.5;       // 斑马线中心世界 z
uniform float crosswalk_depth = 2.6;           // 斑马线纵深 (行驶方向, 米)
uniform float crosswalk_span_half = 3.6;       // 横向半宽 (米, x 从 -span 到 +span)
uniform float crosswalk_stripe_w = 0.45;       // 单条白条宽度 (米)
uniform float crosswalk_gap = 0.45;            // 条间空隙 (米)
uniform float crosswalk_roughness : hint_range(0.0, 1.0, 0.01) = 0.55;
uniform float crosswalk_feather : hint_range(0.001, 0.2, 0.001) = 0.025;

varying vec3 world_pos;
varying float v_paint;   // 标线漆面系数 (fragment 内赋值): 阻尼镜面高光防削顶
varying float v_ao;      // AO 透传 (light() 中供环境填充项使用)

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
	float edge_stripe_mix = 0.0;
	float cw_mix = 0.0;
	AO = texture(ao_texture, uv).r;
	v_ao = AO;
	AO_LIGHT_AFFECT = 0.85;

	// 路缘白实线: 世界 x 距路缘 < line_width 处采样 RGBA 标线贴花,
	// u = 横穿 0.2m 线宽, v = 沿车道里程周期循环; 贴花 alpha 驱动混合与白漆压粗糙度
	if (edge_stripe_line_width > 0.0) {
		float dx = abs(world_pos.x - edge_stripe_center);
		float d_edge = edge_stripe_half_width - dx;     // 距路缘的横向距离
		float m = 1.0 - smoothstep(edge_stripe_line_width - edge_stripe_feather,
				edge_stripe_line_width + edge_stripe_feather, d_edge);
		if (m > 0.001) {
			float t = clamp(d_edge / edge_stripe_line_width, 0.0, 1.0);
			float sv = fract(world_pos.z / edge_stripe_world_period);
			vec4 stripe_col = texture(edge_stripe_texture, vec2(t, sv));
			float w = m * stripe_col.a;
			ALBEDO = mix(ALBEDO, stripe_col.rgb, w);
			rough = mix(rough, edge_stripe_roughness, w);
			edge_stripe_mix = w;
		}
	}

	// 过街斑马线: 世界 z 距中心 < depth/2 且 |x| < span 处, 周期白条 (x 向平移半周期错缝)
	float dz = abs(world_pos.z - crosswalk_center_z);
	float in_depth = 1.0 - smoothstep(crosswalk_depth * 0.5 - crosswalk_feather,
			crosswalk_depth * 0.5 + crosswalk_feather, dz);
	float in_span = 1.0 - smoothstep(crosswalk_span_half - crosswalk_feather,
			crosswalk_span_half + crosswalk_feather, abs(world_pos.x));
	if (in_depth * in_span > 0.001) {
		float period = crosswalk_stripe_w + crosswalk_gap;
		float sx = world_pos.x / period;              // 连续条纹坐标
		float stripe = abs(fract(sx) - 0.5) * 2.0;    // 0..1 三角波
		float m = (1.0 - smoothstep(crosswalk_stripe_w / period - crosswalk_feather / period * 4.0,
				crosswalk_stripe_w / period + crosswalk_feather / period * 4.0, stripe))
				* in_depth * in_span;
		if (m > 0.001) {
			// 白漆微磨损: 低频噪声调 alpha, 边缘完整
			float wear = 0.90 + 0.10 * sin(world_pos.z * 2.1 + world_pos.x * 0.7);
			float w = m * wear;
			ALBEDO = mix(ALBEDO, vec3(0.845, 0.860, 0.880), w);   // #E8ECF0 x 0.93 防饱和
			rough = mix(rough, crosswalk_roughness, w);
			cw_mix = w;
		}
	}
	ROUGHNESS = clamp(rough, 0.0, 1.0);
	SPECULAR = 0.5;
	v_paint = clamp(edge_stripe_mix + cw_mix, 0.0, 1.0);
	// 无 EMISSION: 天光反射由 roughness + 环境反射探针的正确 PBR 路径呈现 (纠偏令)
}

void light() {
	// 1. 半兰伯特 + 宽平滑阶梯: lit 不乘 ATTENUATION (阴影由 direct 因子单独压暗),
	//    投影路面保留 45% 冷调直射 => 日式蓝灰阴影, 拒绝刀割死黑
	float ndl = dot(NORMAL, LIGHT);
	float half_lambert = clamp(ndl * 0.5 + 0.5, 0.0, 1.0);
	float w = ramp_smoothness * 0.5;
	float lit = smoothstep(ramp_threshold - w, ramp_threshold + w, half_lambert);
	vec3 tint = mix(shadow_tint.rgb * (1.0 - shadow_strength), vec3(1.0), lit);
	float direct = mix(0.45, 1.0, ATTENUATION);
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * tint * direct * diffuse_gain * (1.0 - v_paint * 0.38);

	// 环境漫射天光填充: 自定义 light() 会丢失引擎 IBL/环境项, 此处按天光色补回
	// (物理 ambient 项, 非 EMISSION 伪天光), 阴影面乘 AO 与天青色 => 拒绝死黑死蓝
	DIFFUSE_LIGHT += ALBEDO * vec3(0.62, 0.72, 0.86) * ambient_fill * v_ao;

	// 2. 粗糙度驱动的柔和镜面: (1-rough)^2 强衰减, 粗糙沥青零闪砂, 白漆留柔光
	vec3 h = normalize(VIEW + LIGHT);
	float nh = clamp(dot(NORMAL, h), 0.0, 1.0);
	float gloss = pow(clamp(1.0 - ROUGHNESS, 0.0, 1.0), 2.0);
	float spec = pow(nh, mix(90.0, 10.0, clamp(ROUGHNESS, 0.0, 1.0))) * gloss;
	SPECULAR_LIGHT += vec3(0.90, 0.95, 1.0) * LIGHT_COLOR * spec * 0.3 * lit * (1.0 - v_paint);

	// 3. 掠角菲涅尔天光 Sheen (冷调蓝灰泛光带, 主脑纠偏项): 菲涅尔边缘按粗糙度
	//    衰减, 阴影区也保留 => 沥青呈湿润冷调而非死平塑料
	float n_dot_v = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float fresnel = pow(1.0 - n_dot_v, 4.0);
	float sheen = fresnel * (1.0 - ROUGHNESS * 0.45) * v_ao * clamp(ambient_fill / 1.4, 0.25, 1.0);
	SPECULAR_LIGHT += vec3(0.62, 0.72, 0.86) * sheen * 0.18 * (1.0 - v_paint);
}
