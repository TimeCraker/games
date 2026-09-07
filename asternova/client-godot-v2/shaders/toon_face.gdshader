shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

// --- 面部基础属性 ---
group_uniforms BaseColor;
uniform vec4 skin_color : source_color = vec4(1.0, 0.96, 0.94, 1.0); // 细腻冷白肌
uniform vec4 blush_color : source_color = vec4(1.0, 0.80, 0.82, 1.0); // 脸颊微粉腮红
uniform sampler2D face_texture : source_color, filter_linear_mipmap;

// --- 面部阴影控制（消除鼻梁/眼眶杂乱多边形三角影）---
group_uniforms FaceShading;
uniform vec4 face_shadow_tint : source_color = vec4(0.92, 0.88, 0.95, 1.0); // 柔和微紫面部阴影
uniform float shadow_threshold : hint_range(0.0, 1.0, 0.01) = 0.45;
uniform float shadow_softness : hint_range(0.001, 0.3, 0.005) = 0.03;
uniform float pitch_clamp : hint_range(0.0, 1.0, 0.05) = 0.15; // 垂直俯角解耦 (大厂标准)
uniform float forward_normal_mix : hint_range(0.0, 1.0, 0.05) = 0.70; // 视口前向平滑法线

void fragment() {
	vec4 tex = texture(face_texture, UV);
	vec4 base = tex * skin_color;
	ALBEDO = base.rgb;
	ROUGHNESS = 0.95;
	SPECULAR = 0.0;
}

void light() {
	// 1. 水平光向量解耦 (大厂工业标准): 压制垂直 Y 倾角, 无论阳光如何俯射, 面部始终水平受光
	vec3 horiz_light = normalize(vec3(LIGHT.x, LIGHT.y * pitch_clamp, LIGHT.z));
	
	// 2. 视口前向法线平滑混合: 彻底抹平鼻梁与眼窝的物理多边形折痕
	vec3 smooth_normal = normalize(mix(NORMAL, vec3(0.0, 0.0, 1.0), forward_normal_mix));

	// 3. 面部平滑半兰伯特
	float NdotL = dot(smooth_normal, horiz_light);
	float half_lambert = clamp(NdotL * 0.5 + 0.5, 0.0, 1.0);
	float light_term = half_lambert * ATTENUATION;
	
	float w = shadow_softness * 0.5;
	float lit_mask = smoothstep(shadow_threshold - w, shadow_threshold + w, light_term);
	vec3 shade_col = mix(face_shadow_tint.rgb * 0.75, vec3(1.0), lit_mask);
	
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * shade_col * ATTENUATION * 0.85;
}
