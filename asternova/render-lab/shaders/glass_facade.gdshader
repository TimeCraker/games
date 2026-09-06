shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled, specular_schlick_ggx;

// AsterNova storefront glass: see-through by day with a soft fresnel
// reflection sheen; double-sided so the flat glass plane reads from both
// the street and the interior.
uniform vec4 albedo_color : source_color = vec4(0.85, 0.95, 1.0, 0.22);
uniform float metallic : hint_range(0.0, 1.0) = 0.35;
uniform float roughness : hint_range(0.0, 1.0) = 0.06;
uniform float fresnel_power : hint_range(0.5, 8.0) = 3.0;
uniform float fresnel_boost : hint_range(0.0, 2.0) = 0.55;
uniform vec3 reflection_tint : source_color = vec3(0.9, 0.96, 1.0);
uniform float reflection_glow : hint_range(0.0, 1.0) = 0.25;

void fragment() {
	float fresnel = pow(1.0 - clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0), fresnel_power);
	ALBEDO = albedo_color.rgb;
	ALPHA = clamp(albedo_color.a + fresnel * fresnel_boost, 0.0, 1.0);
	METALLIC = metallic;
	ROUGHNESS = roughness;
	SPECULAR = 0.6;
	EMISSION = reflection_tint * fresnel * reflection_glow;
}
