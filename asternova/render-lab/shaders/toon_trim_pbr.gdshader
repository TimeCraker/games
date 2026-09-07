shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

// ==============================================================================
// AsterNova - 日系近未来建筑 Trim Sheet 工业着色器 (PBR + NPR 混合体系)
// 专为构件库 (Modular Facade Kit) 与万能装饰贴图 (Trim Sheet) 设计
// 特性：
//   1. 完整 PBR 贴图槽位 (Albedo / Normal / Roughness / Metallic / AO / Emission)
//   2. 二次元赛璐璐受控明暗阶梯 (Toon Ramp) + 蓝紫冷色阴影倾向 (Shadow Tint)
//   3. 倒角高光提取 (Chamfer Bevel Specular)：在受光边缘切出锐利的 3A 工业高光线条
//   4. 结构缝凹陷遮挡 (Cavity AO)：缝隙深处自然压暗，杜绝大灰平面的漂浮塑料感
//   5. 适配 Forward+ 聚类光照与 AgX 色调映射 (Master Tone 保持)
// ==============================================================================

// --- 基础色彩与贴图 ---
group_uniforms BaseColor;
uniform vec4 albedo_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform vec2 uv_scale = vec2(1.0, 1.0);
uniform vec2 uv_offset = vec2(0.0, 0.0);

// --- 表面法线与倒角凹凸 ---
group_uniforms NormalMap;
uniform bool use_normal_map = true;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float normal_depth : hint_range(0.0, 3.0, 0.05) = 1.0;

// --- 微表面粗糙度与金属度 ---
group_uniforms MicroSurface;
uniform sampler2D roughness_texture : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float roughness_scale : hint_range(0.0, 2.0, 0.05) = 1.0;
uniform sampler2D metallic_texture : hint_default_black, filter_linear_mipmap, repeat_enable;
uniform float metallic_scale : hint_range(0.0, 1.0, 0.05) = 1.0;

// --- 缝隙环境遮挡 (Cavity AO) ---
group_uniforms AmbientOcclusion;
uniform sampler2D ao_texture : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float ao_light_affect : hint_range(0.0, 1.0, 0.05) = 0.75;

// --- 二次元赛璐璐阶梯 (Toon Shading) ---
group_uniforms ToonShading;
uniform vec4 shadow_tint : source_color = vec4(0.72, 0.78, 0.90, 1.0); // 清冷天光背阴偏色
uniform float ramp_threshold : hint_range(0.0, 1.0, 0.01) = 0.45;
uniform float ramp_smoothness : hint_range(0.001, 0.4, 0.005) = 0.06;
uniform float shadow_strength : hint_range(0.0, 1.0, 0.05) = 0.50; // 0.50 保证暗部仍有微通透层次

// --- 倒角高光与金属反光 (Bevel & Specular) ---
group_uniforms SpecularHighlight;
uniform float specular_power : hint_range(0.0, 2.0, 0.05) = 1.0;
uniform vec4 specular_tint : source_color = vec4(1.0, 0.97, 0.92, 1.0); // 暖金受光高光
uniform float bevel_specular_sharpness : hint_range(8.0, 128.0, 2.0) = 32.0;

// --- 标识发光 (Signage / Warning Emission) ---
group_uniforms Emission;
uniform bool use_emission = false;
uniform sampler2D emission_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 emission_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float emission_energy : hint_range(0.0, 8.0, 0.1) = 1.0;

varying vec3 v_world_pos;
varying vec3 v_world_normal;

void vertex() {
	v_world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 uv = UV * uv_scale + uv_offset;
	
	// 基础色彩
	vec4 base_tex = texture(albedo_texture, uv);
	ALBEDO = base_tex.rgb * albedo_color.rgb;
	ALPHA = base_tex.a * albedo_color.a;
	
	// 法线 (倒角与凹缝核心)
	if (use_normal_map) {
		vec3 n = texture(normal_texture, uv).rgb * 2.0 - 1.0;
		n.xy *= normal_depth;
		NORMAL = normalize(TANGENT * n.x + BINORMAL * n.y + NORMAL * n.z);
	}
	
	// 粗糙度与金属度
	ROUGHNESS = clamp(texture(roughness_texture, uv).r * roughness_scale, 0.04, 1.0);
	METALLIC = clamp(texture(metallic_texture, uv).r * metallic_scale, 0.0, 1.0);
	
	// AO 烘焙凹槽
	AO = texture(ao_texture, uv).r;
	AO_LIGHT_AFFECT = ao_light_affect;
	
	// 发光标识 (如警示红绿指示灯、荧光条)
	if (use_emission) {
		vec3 emit_tex = texture(emission_texture, uv).rgb;
		EMISSION = emit_tex * emission_color.rgb * emission_energy;
	}
}

void light() {
	// NdotL 光照基础
	float ndotl = dot(NORMAL, LIGHT);
	float half_lambert = clamp(ndotl * 0.5 + 0.5, 0.0, 1.0);
	
	// 赛璐璐阶梯计算
	float ramp_min = ramp_threshold - ramp_smoothness * 0.5;
	float ramp_max = ramp_threshold + ramp_smoothness * 0.5;
	float toon_factor = smoothstep(ramp_min, ramp_max, half_lambert);
	
	// 融入 AO 压暗缝隙
	float raw_ao = mix(1.0, AO, ao_light_affect);
	toon_factor *= raw_ao;
	
	// 阴影着色与冷暖对撞 (受光直接光 + 背光清冷暗部)
	vec3 lit_color = LIGHT_COLOR * ATTENUATION;
	vec3 shadowed_color = lit_color * mix(shadow_tint.rgb, vec3(1.0), 1.0 - shadow_strength);
	vec3 diffuse_light = mix(shadowed_color, lit_color, toon_factor);
	
	DIFFUSE_LIGHT += diffuse_light * ALBEDO;
	
	// 倒角与金属 GGX 镜面高光 (仅在受光侧呈现，切出精致高光边缘)
	if (ndotl > 0.0) {
		vec3 half_vec = normalize(VIEW + LIGHT);
		float ndoth = max(dot(NORMAL, half_vec), 0.0);
		
		// 锐利微倒角高光
		float spec = pow(ndoth, bevel_specular_sharpness);
		spec *= (1.0 - ROUGHNESS * 0.7); // 越光亮倒角越锐
		
		vec3 spec_col = mix(specular_tint.rgb, ALBEDO, METALLIC);
		SPECULAR_LIGHT += spec * spec_col * LIGHT_COLOR * ATTENUATION * specular_power * toon_factor;
	}
}
