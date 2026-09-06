shader_type spatial;
render_mode cull_front, unshaded;

// --- 描边参数 ---
uniform vec4 outline_color : source_color = vec4(0.22, 0.24, 0.32, 1.0); // 日系深灰蓝描边（非死黑）
uniform float outline_thickness : hint_range(0.0005, 0.05, 0.0005) = 0.0035; // 描边粗细
uniform bool distance_scaling = true; // 随相机距离自适应保持恒定视线粗细

void vertex() {
	float factor = 1.0;
	if (distance_scaling) {
		float dist = length(MODELVIEW_MATRIX[3].xyz);
		factor = clamp(dist * 0.35, 0.8, 4.0);
	}
	VERTEX += NORMAL * outline_thickness * factor;
}

void fragment() {
	ALBEDO = outline_color.rgb;
	ALPHA = outline_color.a;
}
