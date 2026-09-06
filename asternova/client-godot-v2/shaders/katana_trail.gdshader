shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

// 太刀月华刀光：银白炽核沿条带中线，向两侧羽化为冰蓝边缘
// UV.x: 0=刀根 -> 1=刀尖 (条带宽度方向)
// UV.y: 0=尾迹最旧 -> 1=挥刀最新 (条带长度方向)

uniform vec4 core_color : source_color = vec4(1.0, 0.99, 0.96, 1.0); // 月华银白炽核
uniform vec4 edge_color : source_color = vec4(0.42, 0.78, 1.0, 1.0); // 冰蓝羽化边缘
uniform float core_width : hint_range(0.02, 0.6, 0.01) = 0.2; // 炽核占半宽比例
uniform float edge_feather : hint_range(0.0, 1.0, 0.01) = 0.55; // 边缘羽化跨度
uniform float intensity : hint_range(0.0, 8.0, 0.05) = 5.0; // 加法混合强度
uniform float tip_boost : hint_range(0.0, 3.0, 0.05) = 1.25; // 刀尖端增亮

void fragment() {
	float d = abs(UV.x - 0.5) * 2.0; // 0=条带中线 1=条带边缘
	// 银白炽核 -> 冰蓝羽化边缘的双段混合
	float core_mask = 1.0 - smoothstep(0.0, core_width, d);
	float edge_mask = 1.0 - smoothstep(core_width * 0.35, core_width + edge_feather, d);
	vec3 col = mix(edge_color.rgb, core_color.rgb, core_mask);
	// 挥刀中条带全亮 (COLOR.a=1)；停手后 CPU 侧按 0.12s 写入衰减
	float fade = COLOR.a * smoothstep(0.0, 0.3, UV.y);
	// 刀尖方向轻微增亮
	col *= mix(1.0, tip_boost, UV.x);
	ALBEDO = col * intensity * edge_mask * fade;
	// blend_add 下用透明度通道携带总能量
	ALPHA = clamp(edge_mask * fade, 0.0, 1.0);
}
