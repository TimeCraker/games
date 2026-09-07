shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

// --- 基础属性 ---
group_uniforms BaseColor;
uniform vec4 albedo_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap;
uniform float desaturation : hint_range(0.0, 1.0, 0.01) = 0.0;
uniform bool use_alpha_scissor = false;
uniform float alpha_scissor_threshold : hint_range(0.0, 1.0, 0.05) = 0.5;

// --- 法线与凹凸褶皱 ---
group_uniforms NormalMap;
uniform bool use_normal_map = false;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap;
uniform float normal_depth : hint_range(0.0, 3.0, 0.1) = 1.0;

// --- 二次元 Toon Ramp 色阶控制 ---
group_uniforms ToonShading;
uniform vec4 shadow_tint : source_color = vec4(0.72, 0.76, 0.88, 1.0); // 日系冷蓝/淡紫暗部偏色
uniform float ramp_threshold : hint_range(0.0, 1.0, 0.01) = 0.48; // 主明暗交界线 (Half-Lambert)
uniform float ramp_smoothness : hint_range(0.001, 0.3, 0.005) = 0.03; // 阴影羽化硬度
uniform float shadow_strength : hint_range(0.0, 1.0, 0.05) = 0.60; // 阴影冷调深度

// --- 二次元边缘光 (Rim Light) ---
group_uniforms RimLight;
uniform bool enable_rim = true;
uniform vec4 rim_color : source_color = vec4(0.68, 0.82, 0.98, 1.0);
uniform float rim_threshold : hint_range(0.0, 1.0, 0.01) = 0.65;
uniform float rim_smoothness : hint_range(0.001, 0.5, 0.005) = 0.04;
uniform float rim_spread : hint_range(0.1, 4.0, 0.1) = 2.2;

// --- 高光 (Stylized Specular) ---
group_uniforms Specular;
uniform vec4 specular_color : source_color = vec4(0.92, 0.95, 1.0, 1.0);
uniform float specular_size : hint_range(0.01, 1.0, 0.01) = 0.06;
uniform float specular_smoothness : hint_range(0.001, 0.2, 0.005) = 0.01;

// --- 面部 SDF 仰角解耦（头部前向区域生效，杜绝正午阳光鼻梁/眼眶碎影）---
group_uniforms FacePitchClamp;
uniform bool enable_face_pitch_clamp = true;
uniform float face_pitch_clamp : hint_range(0.0, 1.0, 0.05) = 0.15; // 主光垂直俯仰角钳制 ±15°
uniform float face_forward_mix : hint_range(0.0, 1.0, 0.05) = 0.70; // 面部法线向前向平滑（抹平多边形折痕）
uniform float head_min_y : hint_range(0.0, 2.0, 0.01) = 1.30; // 模型空间头部区域下缘（Aster 1.65m）

// --- 发丝各向异性天使光环 (Kajiya-Kay) ---
group_uniforms HairKajiyaKay;
uniform bool enable_hair_specular = true;
uniform vec4 hair_spec_color : source_color = vec4(0.78, 0.88, 1.0, 1.0); // 冷蓝月华
uniform float hair_spec_strength : hint_range(0.0, 1.0, 0.01) = 0.30;
uniform float hair_shininess : hint_range(4.0, 128.0, 1.0) = 40.0;

void fragment() {
	vec4 tex_color = texture(albedo_texture, UV);
	vec3 desat = mix(tex_color.rgb, vec3(dot(tex_color.rgb, vec3(0.299, 0.587, 0.114))), desaturation);
	vec3 base = desat * albedo_color.rgb;
	ALBEDO = base;
	ALPHA = tex_color.a * albedo_color.a;
	if (use_alpha_scissor) {
		ALPHA_SCISSOR_THRESHOLD = alpha_scissor_threshold;
	}
	if (use_normal_map) {
		NORMAL_MAP = texture(normal_texture, UV).xyz;
		NORMAL_MAP_DEPTH = normal_depth;
	}
	ROUGHNESS = 0.85;
	SPECULAR = 0.0;
}

varying float v_head_mask;      // 模型空间头部区域掩码
varying float v_front_mask;     // 头部前向（面部）掩码
varying vec3 v_world_up_view;   // 视空间下的世界竖直轴（俯仰钳制基准）
varying vec3 v_face_fwd_view;   // 视空间下的面部前向（模型 rest -Z）
varying vec3 v_strand_dir;      // 视空间发流方向（Kajiya-Kay 切线代理）

void vertex() {
	v_head_mask = step(head_min_y, VERTEX.y);
	v_front_mask = smoothstep(0.05, 0.45, -NORMAL.z); // 面部朝 -Z
	mat3 model_rot = mat3(MODEL_MATRIX);
	v_world_up_view = normalize((MODELVIEW_MATRIX * vec4(transpose(model_rot) * vec3(0.0, 1.0, 0.0), 0.0)).xyz);
	v_face_fwd_view = normalize((MODELVIEW_MATRIX * vec4(0.0, 0.0, -1.0, 0.0)).xyz);
	// 发簇沿 +Y 生长：以模型上方向作为 Kajiya-Kay 切线代理（网格无 TANGENT 属性）
	v_strand_dir = normalize((MODELVIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
}

void light() {
	// 1. 半兰伯特光照 (Half-Lambert) 计算，将 [-1, 1] 映射到 [0, 1]
	float NdotL = dot(NORMAL, LIGHT);
	float half_lambert = clamp(NdotL * 0.5 + 0.5, 0.0, 1.0);
	float light_term = half_lambert * ATTENUATION;

	// 1.5 面部 SDF 仰角解耦：头部前向区域改用「俯仰钳制光向量 × 前向平滑法线」重算明暗项
	//     光向量沿真实世界竖直轴分解后钳制俯仰角（±15°），与相机姿态无关
	if (enable_face_pitch_clamp && v_head_mask > 0.001 && v_front_mask > 0.001) {
		vec3 up_v = normalize(v_world_up_view);
		float L_vert = dot(LIGHT, up_v);
		vec3 L_clamped = normalize(LIGHT - up_v * L_vert + up_v * (L_vert * face_pitch_clamp));
		vec3 N_face = normalize(mix(NORMAL, normalize(v_face_fwd_view), face_forward_mix));
		float face_term = clamp(dot(N_face, L_clamped) * 0.5 + 0.5, 0.0, 1.0) * ATTENUATION;
		light_term = mix(light_term, face_term, v_head_mask * v_front_mask);
	}

	// 2. 赛璐璐两阶光照阶梯
	float w = ramp_smoothness * 0.5;
	float lit_mask = smoothstep(ramp_threshold - w, ramp_threshold + w, light_term);
	float mid_mask = smoothstep(0.22 - w, 0.22 + w, light_term);

	// 亮部 1.0，中间过渡层加入冷紫阴影调色，暗部完全归零（由环境光呈现）
	vec3 light_mult = mix(vec3(0.0), shadow_tint.rgb * (1.0 - shadow_strength), mid_mask);
	light_mult = mix(light_mult, vec3(1.0), lit_mask);

	// 3. 二次元边缘轮廓光 (Rim Light) - 仅在受光侧呈现
	vec3 rim_contribution = vec3(0.0);
	if (enable_rim) {
		float NdotV = dot(NORMAL, VIEW);
		float rim_raw = clamp(1.0 - clamp(NdotV, 0.0, 1.0), 0.0, 1.0);
		float rim_intensity = smoothstep(rim_threshold - 0.03, rim_threshold + 0.03, pow(rim_raw, rim_spread));
		rim_contribution = rim_intensity * rim_color.rgb * LIGHT_COLOR * 0.35 * lit_mask;
	}

	// 4. 二次元高光 (Specular)
	vec3 half_vector = normalize(VIEW + LIGHT);
	float NdotH = dot(NORMAL, half_vector);
	float spec_intensity = smoothstep(1.0 - specular_size - 0.01, 1.0 - specular_size + 0.01, NdotH);
	vec3 specular_contribution = spec_intensity * specular_color.rgb * LIGHT_COLOR * 0.45 * lit_mask;

	// 4.5 发丝 Kajiya-Kay 各向异性天使光环：垂直于发流的镜面角形成弧形高光带
	vec3 strand_contribution = vec3(0.0);
	if (enable_hair_specular && v_head_mask > 0.5) {
		float TdotH = dot(normalize(v_strand_dir), half_vector);
		float sinTH = sqrt(max(0.0, 1.0 - TdotH * TdotH));
		float strand = pow(sinTH, hair_shininess) * hair_spec_strength * lit_mask;
		strand_contribution = strand * hair_spec_color.rgb * LIGHT_COLOR;
	}

	// 5. 漫反射贡献累加（乘以 0.90 控光系数，配合环境光维持最高亮度在 0.88~0.92，细腻保留高光与布纹细节）
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * light_mult * ATTENUATION * 0.90;
	SPECULAR_LIGHT += specular_contribution + rim_contribution + strand_contribution;
}
