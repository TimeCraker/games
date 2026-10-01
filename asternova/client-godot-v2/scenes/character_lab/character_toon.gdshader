shader_type spatial;
render_mode cull_disabled, specular_disabled;

uniform sampler2D albedo_texture : source_color, filter_linear_mipmap_anisotropic;
uniform vec4 albedo_color : source_color = vec4(1.0);
uniform vec3 shadow_tint : source_color = vec3(0.66, 0.72, 0.88);

void fragment() {
	// These characters have opaque JPG albedo. Do not write ALPHA: doing so
	// routes even alpha=1 fragments through transparent sorting in Godot.
	ALBEDO = texture(albedo_texture, UV).rgb * albedo_color.rgb;
	ROUGHNESS = 0.85;
}

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float band = smoothstep(0.12, 0.18, ndl);
	vec3 tint = mix(shadow_tint * 0.32, vec3(0.75), band);
	DIFFUSE_LIGHT += ALBEDO * tint * LIGHT_COLOR * ATTENUATION;
}
