shader_type spatial;
render_mode unshaded;

uniform sampler2D face_albedo : source_color, filter_linear_mipmap;
uniform vec4 tint : source_color = vec4(1.0);

void fragment() {
	vec3 world_normal = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	float diffuse = dot(world_normal, normalize(vec3(-0.4, 0.7, 0.5)));
	float soft_shade = mix(0.84, 1.0, smoothstep(-0.25, 0.6, diffuse));
	// Keep the jaw and neck readable without a hard band across the painted eyes.
	ALBEDO = texture(face_albedo, UV).rgb * tint.rgb * soft_shade * 1.6;
}
