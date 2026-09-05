shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled;

// --- 基础属性 ---
group_uniforms BaseColor;
uniform vec4 albedo_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap;
uniform bool use_alpha_scissor = true;
uniform float alpha_scissor_threshold : hint_range(0.0, 1.0, 0.05) = 0.5;

// --- 二次元 Toon Ramp ---
group_uniforms ToonShading;
uniform vec4 shadow_tint : source_color = vec4(0.80, 0.82, 0.92, 1.0); // 柔和淡紫冷调阴影
uniform float ramp_threshold : hint_range(0.0, 1.0, 0.01) = 0.45;
uniform float ramp_smoothness : hint_range(0.001, 0.3, 0.005) = 0.04;
uniform float shadow_strength : hint_range(0.0, 1.0, 0.05) = 0.45;

// --- 二次元发丝边缘光 ---
group_uniforms RimLight;
uniform bool enable_rim = true;
uniform vec4 rim_color : source_color = vec4(0.85, 0.92, 1.0, 1.0);
uniform float rim_threshold : hint_range(0.0, 1.0, 0.01) = 0.60;
uniform float rim_smoothness : hint_range(0.001, 0.5, 0.005) = 0.05;
uniform float rim_spread : hint_range(0.1, 4.0, 0.1) = 2.0;

void fragment() {
	vec4 tex_color = texture(albedo_texture, UV);
	ALBEDO = tex_color.rgb * albedo_color.rgb;
	ALPHA = tex_color.a * albedo_color.a;
	if (use_alpha_scissor) {
		ALPHA_SCISSOR_THRESHOLD = alpha_scissor_threshold;
	}
	ROUGHNESS = 0.75;
	SPECULAR = 0.0;
}

void light() {
	float NdotL = dot(NORMAL, LIGHT);
	float half_lambert = clamp(NdotL * 0.5 + 0.5, 0.0, 1.0);
	float light_term = half_lambert * ATTENUATION;

	float w = ramp_smoothness * 0.5;
	float lit_mask = smoothstep(ramp_threshold - w, ramp_threshold + w, light_term);
	float mid_mask = smoothstep(0.20 - w, 0.20 + w, light_term);

	vec3 light_mult = mix(vec3(0.0), shadow_tint.rgb * (1.0 - shadow_strength), mid_mask);
	light_mult = mix(light_mult, vec3(1.0), lit_mask);

	vec3 rim_contribution = vec3(0.0);
	if (enable_rim) {
		float NdotV = dot(NORMAL, VIEW);
		float rim_raw = clamp(1.0 - clamp(NdotV, 0.0, 1.0), 0.0, 1.0);
		float rim_intensity = smoothstep(rim_threshold - 0.03, rim_threshold + 0.03, pow(rim_raw, rim_spread));
		rim_contribution = rim_intensity * rim_color.rgb * LIGHT_COLOR * 0.25 * lit_mask;
	}

	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * light_mult * ATTENUATION * 0.92;
	SPECULAR_LIGHT += rim_contribution;
}
