"""
Build Aster's Katana '星霜月华' (Seisou Gekka) 3D Model
Blender 5.2 Python Script with Automated High-Definition Composite Showcase

Outputs:
- aster_katana.blend (Dual-mesh: Blade_Mesh & Scabbard_Mesh at (0,0,0))
- aster_katana.glb (Game-ready GLTF binary)
- textures/tex_katana_basecolor.png (2048x2048 atlas)
- katana_preview.png (Museum-grade multi-view presentation board)
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler
import os

# --- Configurations & Paths ---
PROJECT_DIR = r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
OUT_DIR = os.path.join(PROJECT_DIR, r"art\models\weapons\aster_katana")
TEX_DIR = os.path.join(OUT_DIR, "textures")
TEX_PATH = os.path.join(TEX_DIR, "tex_katana_basecolor.png")
BLEND_OUT = os.path.join(OUT_DIR, "aster_katana.blend")
GLB_OUT = os.path.join(OUT_DIR, "aster_katana.glb")
PREVIEW_OUT = os.path.join(OUT_DIR, "katana_preview.png")

TEMP_RENDER_DIR = os.path.join(OUT_DIR, "temp_renders")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TEX_DIR, exist_ok=True)
os.makedirs(TEMP_RENDER_DIR, exist_ok=True)

# Curvature Formula (Sori)
def sori(z):
    if z > 0:
        return -0.002 * (z / 0.25)
    t = abs(z) / 0.70
    return 0.018 * (t ** 1.35)

# --- Materials Setup ---
def create_materials():
    mats = {}
    tex_img = None
    if os.path.exists(TEX_PATH):
        tex_img = bpy.data.images.load(TEX_PATH)
        tex_img.name = "Tex_Katana_BaseColor"
    
    mat_configs = {
        "M_Katana_Saya": {
            "color": (0.88, 0.88, 0.92, 1.0), # #E0E0E8
            "metallic": 0.05,
            "roughness": 0.28,
            "tex_blend": 0.90
        },
        "M_Katana_Gold": {
            "color": (0.92, 0.77, 0.48, 1.0), # #EBC57A
            "metallic": 0.85,
            "roughness": 0.28,
            "tex_blend": 0.85
        },
        "M_Katana_Blade": {
            "color": (0.91, 0.93, 0.96, 1.0), # #E8EEF5
            "metallic": 0.96,
            "roughness": 0.16,
            "tex_blend": 0.95
        },
        "M_Katana_Tsuka": {
            "color": (0.96, 0.96, 0.98, 1.0), # #F4F5FA
            "metallic": 0.0,
            "roughness": 0.50,
            "tex_blend": 0.95
        },
        "M_Katana_Ribbon": {
            "color": (0.68, 0.82, 0.98, 1.0), # #AED1FA
            "metallic": 0.0,
            "roughness": 0.55,
            "tex_blend": 0.85
        },
        "M_Katana_Gem": {
            "color": (0.37, 0.82, 0.93, 1.0), # #5FD2EE
            "metallic": 0.15,
            "roughness": 0.06,
            "tex_blend": 0.95,
            "emission": (0.37, 0.82, 0.93, 1.0),
            "emission_strength": 0.6
        },
        "M_Katana_Outline": {
            "color": (0.24, 0.26, 0.36, 1.0), # #3D435C
            "unshaded": True
        }
    }
    
    for name, cfg in mat_configs.items():
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        
        output = nodes.new(type="ShaderNodeOutputMaterial")
        output.location = (400, 0)
        
        if cfg.get("unshaded"):
            mat.use_backface_culling = True
            emit = nodes.new(type="ShaderNodeEmission")
            emit.inputs['Color'].default_value = cfg["color"]
            emit.inputs['Strength'].default_value = 1.0
            links.new(emit.outputs['Emission'], output.inputs['Surface'])
            mats[name] = mat
            continue
            
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs['Base Color'].default_value = cfg["color"]
        bsdf.inputs['Metallic'].default_value = cfg["metallic"]
        bsdf.inputs['Roughness'].default_value = cfg["roughness"]
        
        if "emission" in cfg:
            bsdf.inputs['Emission Color'].default_value = cfg["emission"]
            bsdf.inputs['Emission Strength'].default_value = cfg["emission_strength"]
            
        if tex_img:
            tex_node = nodes.new(type="ShaderNodeTexImage")
            tex_node.location = (-350, 0)
            tex_node.image = tex_img
            
            mix = nodes.new(type="ShaderNodeMix")
            mix.location = (-100, 100)
            mix.data_type = 'RGBA'
            mix.clamp_result = True
            mix.inputs['Factor'].default_value = cfg["tex_blend"]
            mix.inputs[6].default_value = cfg["color"]
            links.new(tex_node.outputs['Color'], mix.inputs[7])
            links.new(mix.outputs[2], bsdf.inputs['Base Color'])
        
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        mats[name] = mat
        
    return mats

# --- Blade Mesh Generator ---
def generate_blade_mesh(materials):
    mesh = bpy.data.meshes.new("Blade_Mesh")
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()
    
    # 1. Blade Body (刀刃)
    n_seg = 20
    blade_rings = []
    
    for i in range(n_seg + 1):
        s = i / n_seg
        z = -0.015 - s * (0.66 - 0.015)
        y_c = sori(z)
        
        width = 0.026 * (1.0 - 0.18 * s)
        thick = 0.0050 * (1.0 - 0.32 * s)
        
        v_ha = bm.verts.new((0.0, y_c - width * 0.60, z))
        v_sr = bm.verts.new((thick * 0.5, y_c - width * 0.05, z))
        v_mr = bm.verts.new((thick * 0.32, y_c + width * 0.40, z))
        v_ml = bm.verts.new((-thick * 0.32, y_c + width * 0.40, z))
        v_sl = bm.verts.new((-thick * 0.5, y_c - width * 0.05, z))
        
        blade_rings.append([v_ha, v_sr, v_mr, v_ml, v_sl])
        
    for i in range(n_seg):
        r0 = blade_rings[i]
        r1 = blade_rings[i+1]
        s0 = (i / n_seg) * 0.5
        s1 = ((i + 1) / n_seg) * 0.5
        
        faces_data = [
            (r0[0], r1[0], r1[1], r0[1], (0.45, s0), (0.45, s1), (0.25, s1), (0.25, s0)), # Edge-R
            (r0[1], r1[1], r1[2], r0[2], (0.25, s0), (0.25, s1), (0.05, s1), (0.05, s0)), # Flat-R
            (r0[2], r1[2], r1[3], r0[3], (0.05, s0), (0.05, s1), (0.02, s1), (0.02, s0)), # Spine
            (r0[3], r1[3], r1[4], r0[4], (0.05, s0), (0.05, s1), (0.25, s1), (0.25, s0)), # Flat-L
            (r0[4], r1[4], r1[0], r0[0], (0.25, s0), (0.25, s1), (0.45, s1), (0.45, s0)), # Edge-L
        ]
        for v1, v2, v3, v4, uv1, uv2, uv3, uv4 in faces_data:
            f = bm.faces.new((v1, v2, v3, v4))
            f.material_index = 2 # M_Katana_Blade
            f.smooth = True
            for l, uv in zip(f.loops, [uv1, uv2, uv3, uv4]):
                l[uv_layer].uv = uv

    # Kissaki (刀尖)
    last_r = blade_rings[-1]
    tip_z = -0.70
    tip_y = sori(tip_z) + 0.006
    v_tip = bm.verts.new((0.0, tip_y, tip_z))
    
    kissaki_faces = [
        (last_r[0], v_tip, last_r[1]),
        (last_r[1], v_tip, last_r[2]),
        (last_r[2], v_tip, last_r[3]),
        (last_r[3], v_tip, last_r[4]),
        (last_r[4], v_tip, last_r[0]),
    ]
    for v1, v2, v3 in kissaki_faces:
        f = bm.faces.new((v1, v2, v3))
        f.material_index = 2
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = (0.35, 0.48)
            
    # 2. Habaki (刀鎺)
    hab_z0 = 0.005
    hab_z1 = -0.022
    w_hab = 0.029
    th_hab = 0.0075
    hab_r0 = [
        bm.verts.new((0.0, sori(hab_z0) - w_hab*0.55, hab_z0)),
        bm.verts.new((th_hab*0.5, sori(hab_z0) - w_hab*0.15, hab_z0)),
        bm.verts.new((th_hab*0.5, sori(hab_z0) + w_hab*0.45, hab_z0)),
        bm.verts.new((0.0, sori(hab_z0) + w_hab*0.50, hab_z0)),
        bm.verts.new((-th_hab*0.5, sori(hab_z0) + w_hab*0.45, hab_z0)),
        bm.verts.new((-th_hab*0.5, sori(hab_z0) - w_hab*0.15, hab_z0)),
    ]
    hab_r1 = [
        bm.verts.new((0.0, sori(hab_z1) - w_hab*0.55, hab_z1)),
        bm.verts.new((th_hab*0.5, sori(hab_z1) - w_hab*0.15, hab_z1)),
        bm.verts.new((th_hab*0.5, sori(hab_z1) + w_hab*0.45, hab_z1)),
        bm.verts.new((0.0, sori(hab_z1) + w_hab*0.50, hab_z1)),
        bm.verts.new((-th_hab*0.5, sori(hab_z1) + w_hab*0.45, hab_z1)),
        bm.verts.new((-th_hab*0.5, sori(hab_z1) - w_hab*0.15, hab_z1)),
    ]
    for j in range(6):
        j_next = (j + 1) % 6
        f = bm.faces.new((hab_r0[j], hab_r1[j], hab_r1[j_next], hab_r0[j_next]))
        f.material_index = 1 # M_Katana_Gold
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = (0.62, 0.38)

    # 3. Tsuba (四芒星护手)
    tsuba_z_mid = 0.010
    tsuba_th = 0.0045
    
    def tsuba_star_perimeter(z_pos):
        pts = []
        for q in range(4):
            base_ang = q * (math.pi / 2.0)
            r_tip = 0.045 if (q % 2 == 1) else 0.038
            pts.append((r_tip * math.cos(base_ang), r_tip * math.sin(base_ang), z_pos))
            ang1 = base_ang + math.radians(22)
            pts.append((0.024 * math.cos(ang1), 0.024 * math.sin(ang1), z_pos))
            ang2 = base_ang + math.radians(45)
            pts.append((0.014 * math.cos(ang2), 0.014 * math.sin(ang2), z_pos))
            ang3 = base_ang + math.radians(68)
            pts.append((0.024 * math.cos(ang3), 0.024 * math.sin(ang3), z_pos))
        return [bm.verts.new(p) for p in pts]

    tsuba_top = tsuba_star_perimeter(tsuba_z_mid + tsuba_th)
    tsuba_bot = tsuba_star_perimeter(tsuba_z_mid - tsuba_th)
    
    for j in range(16):
        j_next = (j + 1) % 16
        f = bm.faces.new((tsuba_top[j], tsuba_bot[j], tsuba_bot[j_next], tsuba_top[j_next]))
        f.material_index = 1 # M_Katana_Gold
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = (0.62, 0.38)

    v_tsuba_hub_top = bm.verts.new((0.0, 0.0, tsuba_z_mid + tsuba_th + 0.002))
    v_tsuba_hub_bot = bm.verts.new((0.0, 0.0, tsuba_z_mid - tsuba_th - 0.002))
    
    for j in range(16):
        j_next = (j + 1) % 16
        f_top = bm.faces.new((tsuba_top[j], tsuba_top[j_next], v_tsuba_hub_top))
        is_petal = (j % 4 == 0 or j % 4 == 3)
        f_top.material_index = 0 if is_petal else 1
        f_top.smooth = True
        for l in f_top.loops:
            l[uv_layer].uv = (0.75, 0.75) if is_petal else (0.62, 0.38)
            
        f_bot = bm.faces.new((tsuba_bot[j_next], tsuba_bot[j], v_tsuba_hub_bot))
        f_bot.material_index = 0 if is_petal else 1
        f_bot.smooth = True
        for l in f_bot.loops:
            l[uv_layer].uv = (0.75, 0.75) if is_petal else (0.62, 0.38)

    # Center Gem on Tsuba
    gem_r = 0.0055
    gem_top = bm.verts.new((0.0, 0.0, tsuba_z_mid + tsuba_th + 0.0055))
    gem_ring = [
        bm.verts.new((0.0, gem_r, tsuba_z_mid + tsuba_th + 0.002)),
        bm.verts.new((gem_r, 0.0, tsuba_z_mid + tsuba_th + 0.002)),
        bm.verts.new((0.0, -gem_r, tsuba_z_mid + tsuba_th + 0.002)),
        bm.verts.new((-gem_r, 0.0, tsuba_z_mid + tsuba_th + 0.002)),
    ]
    for k in range(4):
        k_next = (k + 1) % 4
        f = bm.faces.new((gem_ring[k], gem_ring[k_next], gem_top))
        f.material_index = 5 # M_Katana_Gem
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = (0.88, 0.12)

    # 4. Tsuka (刀柄)
    tsuka_n = 12
    tsuka_rings = []
    w_t0, th_t0 = 0.0155, 0.0105
    
    for i in range(tsuka_n + 1):
        s = i / tsuka_n
        z = 0.015 + s * (0.245 - 0.015)
        y_c = sori(z)
        
        waist = 1.0 - 0.12 * math.sin(s * math.pi)
        wy = w_t0 * waist
        wx = th_t0 * waist
        
        ring_v = []
        for a_idx in range(8):
            ang = a_idx * math.pi / 4.0
            vx = wx * math.sin(ang)
            vy = y_c + wy * math.cos(ang)
            ring_v.append(bm.verts.new((vx, vy, z)))
        tsuka_rings.append(ring_v)
        
    for i in range(tsuka_n):
        r0 = tsuka_rings[i]
        r1 = tsuka_rings[i+1]
        s0 = i / tsuka_n
        s1 = (i + 1) / tsuka_n
        
        for j in range(8):
            j_next = (j + 1) % 8
            f = bm.faces.new((r0[j], r1[j], r1[j_next], r0[j_next]))
            if i == 0:
                f.material_index = 1 # Fuchi collar
                f.smooth = True
                for l in f.loops:
                    l[uv_layer].uv = (0.62, 0.38)
            else:
                f.material_index = 3 # Tsuka wrap
                f.smooth = True
                u0 = (j / 8.0) * 0.5
                u1 = ((j + 1) / 8.0) * 0.5
                v0 = 0.5 + s0 * 0.5
                v1 = 0.5 + s1 * 0.5
                f.loops[0][uv_layer].uv = (u0, v0)
                f.loops[1][uv_layer].uv = (u0, v1)
                f.loops[2][uv_layer].uv = (u1, v1)
                f.loops[3][uv_layer].uv = (u1, v0)

    # Kashira (柄首) Gold Dome
    last_t_ring = tsuka_rings[-1]
    v_kashira_top = bm.verts.new((0.0, sori(0.255), 0.255))
    for j in range(8):
        j_next = (j + 1) % 8
        f = bm.faces.new((last_t_ring[j], last_t_ring[j_next], v_kashira_top))
        f.material_index = 1
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = (0.62, 0.38)

    # 5. Kashira Tassel (柄尾小星芒吊坠)
    ring_z = 0.252
    base_y = sori(ring_z)
    
    cord_pts_1 = [
        (0.002, base_y - 0.010, ring_z),
        (0.003, base_y - 0.040, ring_z - 0.002),
        (0.002, base_y - 0.070, ring_z - 0.004),
    ]
    cord_pts_2 = [
        (-0.002, base_y - 0.010, ring_z),
        (-0.003, base_y - 0.035, ring_z + 0.002),
        (-0.002, base_y - 0.060, ring_z + 0.003),
    ]
    
    def build_tassel_strip(pts, width=0.0035, mat_idx=4):
        v_pairs = []
        for px, py, pz in pts:
            vl = bm.verts.new((px, py, pz - width*0.5))
            vr = bm.verts.new((px, py, pz + width*0.5))
            v_pairs.append((vl, vr))
        for k in range(len(pts) - 1):
            vl0, vr0 = v_pairs[k]
            vl1, vr1 = v_pairs[k+1]
            f = bm.faces.new((vl0, vl1, vr1, vr0))
            f.material_index = mat_idx
            f.smooth = True
            for l in f.loops:
                l[uv_layer].uv = (0.88, 0.38)
                
    build_tassel_strip(cord_pts_1)
    build_tassel_strip(cord_pts_2)
    
    pend_y = base_y - 0.082
    pend_z = ring_z - 0.004
    pend_pts = [
        bm.verts.new((0.0, pend_y + 0.012, pend_z)),
        bm.verts.new((0.0, pend_y + 0.0035, pend_z + 0.0035)),
        bm.verts.new((0.0, pend_y, pend_z + 0.011)),
        bm.verts.new((0.0, pend_y - 0.0035, pend_z + 0.0035)),
        bm.verts.new((0.0, pend_y - 0.012, pend_z)),
        bm.verts.new((0.0, pend_y - 0.0035, pend_z - 0.0035)),
        bm.verts.new((0.0, pend_y, pend_z - 0.011)),
        bm.verts.new((0.0, pend_y + 0.0035, pend_z - 0.0035)),
    ]
    v_pend_center = bm.verts.new((0.0, pend_y, pend_z))
    for k in range(8):
        k_next = (k + 1) % 8
        f = bm.faces.new((pend_pts[k], pend_pts[k_next], v_pend_center))
        f.material_index = 1 # M_Katana_Gold
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = (0.62, 0.38)
            
    f_gem = bm.faces.new((pend_pts[1], pend_pts[3], pend_pts[5], pend_pts[7]))
    f_gem.material_index = 5 # M_Katana_Gem
    for l in f_gem.loops:
        l[uv_layer].uv = (0.88, 0.12)

    bm.to_mesh(mesh)
    bm.free()
    
    # 6 Base Materials
    base_mat_keys = ["M_Katana_Saya", "M_Katana_Gold", "M_Katana_Blade", "M_Katana_Tsuka", "M_Katana_Ribbon", "M_Katana_Gem"]
    for mat_name in base_mat_keys:
        mesh.materials.append(materials[mat_name])
        
    # Append 6 outline slots for Solidify material offset
    for _ in range(6):
        mesh.materials.append(materials["M_Katana_Outline"])
        
    obj = bpy.data.objects.new("Blade_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (0.0, 0.0, 0.0)
    return obj

# --- Scabbard Mesh Generator ---
def generate_scabbard_mesh(materials):
    mesh = bpy.data.meshes.new("Scabbard_Mesh")
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()
    
    # 1. Koiguchi (刀鞘口)
    koi_z0 = 0.001
    koi_z1 = -0.016
    w_k, th_k = 0.0185, 0.0125
    
    koi_r0 = []
    koi_r1 = []
    for a_idx in range(8):
        ang = a_idx * math.pi / 4.0
        vx = th_k * math.sin(ang)
        vy0 = sori(koi_z0) + w_k * math.cos(ang)
        vy1 = sori(koi_z1) + w_k * math.cos(ang)
        koi_r0.append(bm.verts.new((vx, vy0, koi_z0)))
        koi_r1.append(bm.verts.new((vx, vy1, koi_z1)))
        
    for j in range(8):
        j_next = (j + 1) % 8
        f = bm.faces.new((koi_r0[j], koi_r1[j], koi_r1[j_next], koi_r0[j_next]))
        f.material_index = 1 # M_Katana_Gold
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = (0.62, 0.38)
            
    # Inner opening lip
    inner_lip = []
    w_in, th_in = 0.0145, 0.0055
    for a_idx in range(8):
        ang = a_idx * math.pi / 4.0
        vx = th_in * math.sin(ang)
        vy = sori(koi_z0) + w_in * math.cos(ang)
        inner_lip.append(bm.verts.new((vx, vy, koi_z0)))
    for j in range(8):
        j_next = (j + 1) % 8
        f = bm.faces.new((inner_lip[j], koi_r0[j], koi_r0[j_next], inner_lip[j_next]))
        f.material_index = 1 # M_Katana_Gold
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = (0.62, 0.38)

    # 2. Saya Body (刀鞘主体)
    n_seg = 20
    saya_rings = [koi_r1]
    
    for i in range(1, n_seg + 1):
        s = i / n_seg
        z = -0.016 - s * (0.68 - 0.016)
        y_c = sori(z)
        
        wy = w_k * (1.0 - 0.20 * s)
        wx = th_k * (1.0 - 0.22 * s)
        
        ring_v = []
        for a_idx in range(8):
            ang = a_idx * math.pi / 4.0
            vx = wx * math.sin(ang)
            vy = y_c + wy * math.cos(ang)
            ring_v.append(bm.verts.new((vx, vy, z)))
        saya_rings.append(ring_v)
        
    for i in range(n_seg):
        r0 = saya_rings[i]
        r1 = saya_rings[i+1]
        s0 = i / n_seg
        s1 = (i + 1) / n_seg
        
        for j in range(8):
            j_next = (j + 1) % 8
            f = bm.faces.new((r0[j], r1[j], r1[j_next], r0[j_next]))
            f.material_index = 0 # M_Katana_Saya
            f.smooth = True
            
            u0 = 0.5 + (j / 8.0) * 0.5
            u1 = 0.5 + ((j + 1) / 8.0) * 0.5
            v0 = 1.0 - s0 * 0.5
            v1 = 1.0 - s1 * 0.5
            f.loops[0][uv_layer].uv = (u0, v0)
            f.loops[1][uv_layer].uv = (u0, v1)
            f.loops[2][uv_layer].uv = (u1, v1)
            f.loops[3][uv_layer].uv = (u1, v0)

    # 3. Sageo (浅蓝缎带蝴蝶结)
    bow_z = -0.050
    bow_x = th_k * 0.95
    bow_y = sori(bow_z) + 0.002
    
    knot_hw = 0.0055
    knot_hh = 0.0065
    knot_d = 0.0045
    k_v = [
        bm.verts.new((bow_x + knot_d, bow_y - knot_hw, bow_z + knot_hh)),
        bm.verts.new((bow_x + knot_d, bow_y + knot_hw, bow_z + knot_hh)),
        bm.verts.new((bow_x + knot_d, bow_y + knot_hw, bow_z - knot_hh)),
        bm.verts.new((bow_x + knot_d, bow_y - knot_hw, bow_z - knot_hh)),
        bm.verts.new((bow_x, bow_y - knot_hw, bow_z + knot_hh)),
        bm.verts.new((bow_x, bow_y + knot_hw, bow_z + knot_hh)),
        bm.verts.new((bow_x, bow_y + knot_hw, bow_z - knot_hh)),
        bm.verts.new((bow_x, bow_y - knot_hw, bow_z - knot_hh)),
    ]
    knot_faces = [
        (k_v[0], k_v[1], k_v[2], k_v[3]),
        (k_v[4], k_v[0], k_v[3], k_v[7]),
        (k_v[1], k_v[5], k_v[6], k_v[2]),
        (k_v[4], k_v[5], k_v[1], k_v[0]),
        (k_v[3], k_v[2], k_v[6], k_v[7]),
    ]
    for face_idx in knot_faces:
        f = bm.faces.new(face_idx)
        f.material_index = 4 # M_Katana_Ribbon
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = (0.88, 0.38)
            
    # 2 Ribbon Loops
    def create_ribbon_loop(direction=1.0):
        loop_w = 0.007
        p0 = Vector((bow_x + 0.002, bow_y, bow_z))
        p1 = Vector((bow_x + 0.007, bow_y + 0.008, bow_z + direction * 0.020))
        p2 = Vector((bow_x + 0.005, bow_y, bow_z + direction * 0.028))
        p3 = Vector((bow_x + 0.001, bow_y - 0.006, bow_z + direction * 0.014))
        
        pts = [p0, p1, p2, p3, p0]
        v_pairs = []
        for p in pts[:-1]:
            vt = bm.verts.new((p.x, p.y + loop_w*0.5, p.z))
            vb = bm.verts.new((p.x, p.y - loop_w*0.5, p.z))
            v_pairs.append((vt, vb))
        for k in range(len(v_pairs)):
            k_next = (k + 1) % len(v_pairs)
            vt0, vb0 = v_pairs[k]
            vt1, vb1 = v_pairs[k_next]
            f = bm.faces.new((vt0, vt1, vb1, vb0))
            f.material_index = 4
            f.smooth = True
            for l in f.loops:
                l[uv_layer].uv = (0.88, 0.38)
                
    create_ribbon_loop(direction=1.0)
    create_ribbon_loop(direction=-1.0)
    
    # 2 Draping Ribbon Tails
    tail_pts_1 = [
        (bow_x + 0.002, bow_y - 0.006, bow_z + 0.004),
        (bow_x + 0.003, bow_y - 0.035, bow_z + 0.006),
        (bow_x + 0.002, bow_y - 0.065, bow_z + 0.004),
    ]
    tail_pts_2 = [
        (bow_x + 0.002, bow_y - 0.006, bow_z - 0.004),
        (bow_x + 0.003, bow_y - 0.030, bow_z - 0.007),
        (bow_x + 0.002, bow_y - 0.055, bow_z - 0.005),
    ]
    
    def create_ribbon_tail(pts, width=0.006):
        v_pairs = []
        for px, py, pz in pts:
            vl = bm.verts.new((px, py, pz - width*0.5))
            vr = bm.verts.new((px, py, pz + width*0.5))
            v_pairs.append((vl, vr))
        for k in range(len(pts) - 1):
            vl0, vr0 = v_pairs[k]
            vl1, vr1 = v_pairs[k+1]
            f = bm.faces.new((vl0, vl1, vr1, vr0))
            f.material_index = 4
            f.smooth = True
            for l in f.loops:
                l[uv_layer].uv = (0.88, 0.38)
        p_tip = pts[-1]
        v_aglet = bm.verts.new((p_tip[0], p_tip[1] - 0.008, p_tip[2]))
        f_aglet = bm.faces.new((v_pairs[-1][0], v_pairs[-1][1], v_aglet))
        f_aglet.material_index = 1 # M_Katana_Gold
        for l in f_aglet.loops:
            l[uv_layer].uv = (0.62, 0.38)

    create_ribbon_tail(tail_pts_1)
    create_ribbon_tail(tail_pts_2)

    # 4. Kojiri (鞘尾)
    last_s_ring = saya_rings[-1]
    koj_z_end = -0.72
    v_koj_tip = bm.verts.new((0.0, sori(koj_z_end), koj_z_end))
    
    for j in range(8):
        j_next = (j + 1) % 8
        f = bm.faces.new((last_s_ring[j], last_s_ring[j_next], v_koj_tip))
        f.material_index = 1 # M_Katana_Gold
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = (0.62, 0.38)

    bm.to_mesh(mesh)
    bm.free()
    
    base_mat_keys = ["M_Katana_Saya", "M_Katana_Gold", "M_Katana_Blade", "M_Katana_Tsuka", "M_Katana_Ribbon", "M_Katana_Gem"]
    for mat_name in base_mat_keys:
        mesh.materials.append(materials[mat_name])
        
    for _ in range(6):
        mesh.materials.append(materials["M_Katana_Outline"])
        
    obj = bpy.data.objects.new("Scabbard_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (0.0, 0.0, 0.0)
    return obj

# --- Inverted Hull Outline Modifier Setup ---
def add_outline_modifier(obj):
    mod = obj.modifiers.new(name="Outline", type='SOLIDIFY')
    mod.thickness = 0.0009 # 0.9mm refined outline
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = 6 # shifts slots 0..5 to 6..11 (M_Katana_Outline)

# --- Main Build & Verification Workflow ---
def main():
    print("=== Starting Aster's Katana 3D Model Generation ===")
    
    # 1. Reset scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # 2. Setup Materials
    mats = create_materials()
    print("Materials initialized:", list(mats.keys()))
    
    # 3. Generate Blade & Scabbard
    blade_obj = generate_blade_mesh(mats)
    scabbard_obj = generate_scabbard_mesh(mats)
    
    # Add NPR inverted hull outline modifiers
    add_outline_modifier(blade_obj)
    add_outline_modifier(scabbard_obj)
    
    # 4. Count Triangles & Vertices
    def count_triangles(obj):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        tri_count = len(bm.faces)
        vert_count = len(bm.verts)
        bm.free()
        return tri_count, vert_count

    blade_tris, blade_verts = count_triangles(blade_obj)
    scabbard_tris, scabbard_verts = count_triangles(scabbard_obj)
    total_tris = blade_tris + scabbard_tris
    
    print("\n" + "="*50)
    print(f"MESH STATISTICS:")
    print(f"Blade_Mesh:    {blade_tris} tris, {blade_verts} verts, Origin: {blade_obj.location}")
    print(f"Scabbard_Mesh: {scabbard_tris} tris, {scabbard_verts} verts, Origin: {scabbard_obj.location}")
    print(f"TOTAL TRIS:    {total_tris} (Target Budget: 800 - 1,500 tris)")
    print("="*50 + "\n")
    
    print(f"Blade_Mesh Dimensions:    {blade_obj.dimensions}")
    print(f"Scabbard_Mesh Dimensions: {scabbard_obj.dimensions}")
    
    # 5. Save Clean Canonical Blender file
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print(f"Saved clean .blend file to: {BLEND_OUT}")
    
    # 6. Export Game-Ready GLB
    bpy.ops.export_scene.gltf(
        filepath=GLB_OUT,
        export_format='GLB',
        use_selection=False,
        export_materials='EXPORT',
        export_image_format='AUTO',
        export_apply=False
    )
    print(f"Exported .glb file to: {GLB_OUT}")
    
    # 7. Render Presentation Views
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.image_settings.file_format = 'PNG'
    
    world = bpy.data.worlds.new("StudioWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.12, 0.13, 0.17, 1.0) # #1F212B
    bg.inputs['Strength'].default_value = 1.0
    
    # Studio Lights
    key_light = bpy.data.lights.new(name="KeyLight", type='SUN')
    key_light.energy = 3.2
    key_light.color = (1.0, 0.90, 0.82)
    key_obj = bpy.data.objects.new("KeyLight", key_light)
    scene.collection.objects.link(key_obj)
    key_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(35))
    
    rim_light = bpy.data.lights.new(name="RimLight", type='SUN')
    rim_light.energy = 2.8
    rim_light.color = (0.68, 0.82, 0.98) # #AED1FA
    rim_obj = bpy.data.objects.new("RimLight", rim_light)
    scene.collection.objects.link(rim_obj)
    rim_obj.rotation_euler = (math.radians(-50), math.radians(-30), math.radians(160))
    
    fill_light = bpy.data.lights.new(name="FillLight", type='SUN')
    fill_light.energy = 1.4
    fill_light.color = (0.72, 0.76, 0.88)
    fill_obj = bpy.data.objects.new("FillLight", fill_light)
    scene.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = (math.radians(25), math.radians(-40), math.radians(-70))
    
    # Camera
    cam_data = bpy.data.cameras.new("RenderCam")
    cam_data.lens = 70
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    # Precise Horizontal Orientation
    rot_hero = Euler((math.radians(90), 0.0, math.radians(-90)))
    
    # Render 1: Sheathed Katana (Full Banner)
    blade_obj.rotation_euler = rot_hero
    scabbard_obj.rotation_euler = rot_hero
    blade_obj.location = (-0.235, 0.0, 0.0)
    scabbard_obj.location = (-0.235, 0.0, 0.0)
    
    cam_obj.location = (0.0, -1.82, 0.0)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)
    
    scene.render.resolution_x = 2400
    scene.render.resolution_y = 520
    path_sheathed = os.path.join(TEMP_RENDER_DIR, "sheathed.png")
    scene.render.filepath = path_sheathed
    bpy.ops.render.render(write_still=True)
    print("Rendered sheathed view.")
    
    # Render 2: Unsheathed Blade & Independent Scabbard (Full Banner)
    # Tighter spacing so both blade and scabbard are completely in frame
    blade_obj.location = (-0.235, 0.0, 0.09)
    scabbard_obj.location = (-0.235, 0.0, -0.11)
    
    scene.render.resolution_x = 2400
    scene.render.resolution_y = 750
    path_unsheathed = os.path.join(TEMP_RENDER_DIR, "unsheathed.png")
    scene.render.filepath = path_unsheathed
    bpy.ops.render.render(write_still=True)
    print("Rendered unsheathed view.")
    
    # Render 3: Close-up of Tsuba (45-degree 3/4 Hero Beauty Angle)
    cam_data.lens = 110
    cam_obj.location = (-0.50, -0.28, 0.22)
    target = Vector((-0.235, 0.0, 0.09))
    direction = target - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    
    scene.render.resolution_x = 760
    scene.render.resolution_y = 600
    path_close_tsuba = os.path.join(TEMP_RENDER_DIR, "close_tsuba.png")
    scene.render.filepath = path_close_tsuba
    bpy.ops.render.render(write_still=True)
    print("Rendered Tsuba 3/4 beauty close-up.")
    
    # Render 4: Close-up of Tsuka & Kashira Tassel
    cam_data.lens = 90
    cam_obj.location = (-0.46, -0.62, 0.02)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)
    path_close_tassel = os.path.join(TEMP_RENDER_DIR, "close_tassel.png")
    scene.render.filepath = path_close_tassel
    bpy.ops.render.render(write_still=True)
    print("Rendered Tassel close-up.")
    
    # Render 5: Close-up of Kissaki & Hamon (Blade Tip)
    cam_data.lens = 95
    cam_obj.location = (+0.42, -0.62, 0.09)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)
    path_close_kissaki = os.path.join(TEMP_RENDER_DIR, "close_kissaki.png")
    scene.render.filepath = path_close_kissaki
    bpy.ops.render.render(write_still=True)
    print("Rendered Kissaki close-up.")
    
    print("All individual renders complete.")

if __name__ == "__main__":
    main()
