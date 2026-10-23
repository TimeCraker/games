shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled;

// 街道道具/建筑 PBR 着色器：贴图 + 可选法线 + 橱窗自发光。
// 光照交给引擎的标准 PBR（不写自定义 light()），随 LightingPreset 正确变化。
// cull_disabled：Tripo 单面片（货架背板/墙板）从背面也要呈现，背面法线在 fragment 里翻转。

group_uniforms BaseColor;
uniform vec4 albedo_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap;
uniform float desaturation : hint_range(0.0, 1.0, 0.01) = 0.0;
uniform bool use_alpha_scissor = false;
uniform float alpha_scissor_threshold : hint_range(0.0, 1.0, 0.05) = 0.5;
uniform float roughness : hint_range(0.0, 1.0, 0.01) = 0.8;

group_uniforms NormalMap;
uniform bool use_normal_map = false;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap;
uniform float normal_depth : hint_range(0.0, 3.0, 0.1) = 1.0;

// 橱窗自发光：优先使用烘焙遮罩；未绑定遮罩时按贴图亮度提取
group_uniforms Emission;
uniform bool enable_emission = false;
uniform bool use_emission_mask = false;
uniform sampler2D emission_mask_texture : filter_linear_mipmap;
uniform vec4 emission_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float emission_energy : hint_range(0.0, 4.0, 0.05) = 0.0;
uniform float emission_min_luminance : hint_range(0.0, 1.0, 0.01) = 0.60;
uniform float emission_mask_softness : hint_range(0.01, 0.5, 0.01) = 0.20;

void fragment() {
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
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
	ROUGHNESS = roughness;
	SPECULAR = 0.5;
	if (enable_emission) {
		float emask = 0.0;
		if (use_emission_mask) {
			emask = texture(emission_mask_texture, UV).r;
		} else {
			float lum = dot(base, vec3(0.299, 0.587, 0.114));
			emask = smoothstep(emission_min_luminance, emission_min_luminance + emission_mask_softness, lum);
		}
		EMISSION += emission_color.rgb * tex_color.rgb * emission_energy * emask;
	}
}
