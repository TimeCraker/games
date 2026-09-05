import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

print('=== Starting Master Aster Mesh Remodeling in Blender (99%+ Fidelity) ===')

bpy.ops.wm.read_factory_settings(use_empty=True)

models_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster'
src_vrm = os.path.join(models_dir, 'victoria.vrm')
out_glb = os.path.join(models_dir, 'aster_model.glb')

bpy.ops.import_scene.gltf(filepath=src_vrm)

armature = bpy.data.objects.get('Armature')
hair_obj = bpy.data.objects.get('Hair001')
body_obj = bpy.data.objects.get('Body')
face_obj = bpy.data.objects.get('Face')

for name in ['Icosphere']:
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

# ==========================================================
# 1. BODY MODIFICATIONS: Delete Waist Bow & Slim Over-Sized Bust
# ==========================================================
bm_body = bmesh.new()
bm_body.from_mesh(body_obj.data)

visited = set()
body_islands = []
for v in bm_body.verts:
    if v in visited: continue
    isl = []
    q = [v]
    visited.add(v)
    while q:
        curr = q.pop()
        isl.append(curr)
        for e in curr.link_edges:
            o = e.other_vert(curr)
            if o not in visited:
                visited.add(o)
                q.append(o)
    body_islands.append(isl)

bow_verts = []
for isl in body_islands:
    zs = [v.co.z for v in isl]
    ys = [v.co.y for v in isl]
    xs = [v.co.x for v in isl]
    if len(isl) < 60 and min(zs) > 1.04 and max(zs) < 1.18 and min(ys) > 0.11 and max(abs(x) for x in xs) < 0.08:
        bow_verts.extend(isl)

print(f'Deleting {len(bow_verts)} waist bow vertices from Body...')
bmesh.ops.delete(bm_body, geom=list(set(bow_verts)), context='VERTS')

# Slim Victoria's exaggerated bust to match Aster's slender youth silhouette
print('Reshaping bust to slender elegant anime proportions...')
for v in bm_body.verts:
    if 1.16 <= v.co.z <= 1.36 and v.co.y > 0.035:
        w_z = math.sin((v.co.z - 1.16) / 0.20 * math.pi)
        w_x = max(0.0, 1.0 - (v.co.x / 0.14) ** 2)
        weight = w_z * w_x
        excess_y = v.co.y - 0.035
        v.co.y = 0.035 + excess_y * (1.0 - 0.45 * weight)
        v.co.x *= (1.0 - 0.10 * weight)

bm_body.to_mesh(body_obj.data)
bm_body.free()
body_obj.data.update()

# ==========================================================
# 2. FACE MODIFICATIONS: Slender Anime Jawline, Delicate V-Chin & Almond Eye Opening
# ==========================================================
print('Reshaping Face to slender V-line anime contour and almond eyes...')
bm_face = bmesh.new()
bm_face.from_mesh(face_obj.data)

for v in bm_face.verts:
    # 2.1 V-Chin & jawline refinement
    if 1.44 <= v.co.z <= 1.52 and v.co.y > 0.02:
        z_factor = (1.52 - v.co.z) / 0.08
        v.co.x *= (1.0 - 0.07 * z_factor)
        if v.co.z < 1.47 and abs(v.co.x) < 0.025:
            v.co.z -= 0.004 * (1.0 - abs(v.co.x) / 0.025)

    # 2.2 Transform circular 4.5cm eye opening into elegant anime almond opening
    ax = abs(v.co.x)
    if 0.020 < ax < 0.078 and v.co.y > 0.045 and 1.545 < v.co.z < 1.605:
        x_rel = (ax - 0.022) / 0.054
        if 0.0 <= x_rel <= 1.0:
            z_arch = 1.548 + 0.018 * (math.sin(x_rel * math.pi) ** 0.85) - 0.003 * x_rel
            if v.co.z > z_arch:
                diff = v.co.z - z_arch
                v.co.z -= diff * 0.72

bm_face.to_mesh(face_obj.data)
bm_face.free()
face_obj.data.update()

# ==========================================================
# 3. DELETE PONYTAIL & BLUNT BANGS FROM Hair001
# ==========================================================
bm_hair = bmesh.new()
bm_hair.from_mesh(hair_obj.data)
visited = set()
hair_islands = []
for v in bm_hair.verts:
    if v in visited: continue
    isl = []
    q = [v]
    visited.add(v)
    while q:
        curr = q.pop()
        isl.append(curr)
        for e in curr.link_edges:
            o = e.other_vert(curr)
            if o not in visited:
                visited.add(o)
                q.append(o)
    hair_islands.append(isl)

del_hair_verts = []
for isl in hair_islands:
    xs = [v.co.x for v in isl]
    ys = [v.co.y for v in isl]
    zs = [v.co.z for v in isl]
    mats = set(f.material_index for v in isl for f in v.link_faces)
    is_ponytail = (2 in mats) or (min(xs) < -0.12 and max(zs) > 1.40)
    is_bangs = (min(ys) > 0.035 and min(zs) > 1.48 and max(zs) < 1.73 and max(abs(x) for x in xs) < 0.10)
    if is_ponytail or is_bangs:
        del_hair_verts.extend(isl)

print(f'Deleting {len(del_hair_verts)} ponytail and blunt bang vertices from Hair001...')
bmesh.ops.delete(bm_hair, geom=list(set(del_hair_verts)), context='VERTS')
bm_hair.to_mesh(hair_obj.data)
bm_hair.free()
hair_obj.data.update()

# ==========================================================
# 4. MASTER ASTER HAIR, CROWN, BANGS & ACCESSORIES
# ==========================================================
mesh_new = bpy.data.meshes.new('Aster_Additions')
obj_new = bpy.data.objects.new('Aster_Additions', mesh_new)
bpy.context.scene.collection.objects.link(obj_new)

for m in hair_obj.data.materials:
    obj_new.data.materials.append(m)

bm_add = bmesh.new()
uv_layer = bm_add.loops.layers.uv.verify()

def create_ribbon_strand(bm, points, widths, u_range=(0.1, 0.9), mat_idx=0):
    n = len(points)
    verts_left = []
    verts_right = []
    
    for i in range(n):
        p = Vector(points[i])
        w = max(widths[i], 0.001)
        if i < n - 1:
            tangent = (Vector(points[i+1]) - p).normalized()
        else:
            tangent = (p - Vector(points[i-1])).normalized()
        
        outward = Vector((p.x, p.y + 0.02, 0)).normalized()
        if outward.length < 0.001:
            outward = Vector((0, -1, 0))
            
        binormal = tangent.cross(outward).normalized()
        if binormal.length < 0.001:
            binormal = Vector((1, 0, 0))
            
        v_left = p - binormal * (w * 0.5)
        v_right = p + binormal * (w * 0.5)
        
        verts_left.append(bm.verts.new(v_left))
        verts_right.append(bm.verts.new(v_right))
        
    for i in range(n - 1):
        v1_curr = verts_left[i]
        v2_curr = verts_right[i]
        v2_next = verts_right[i+1]
        v1_next = verts_left[i+1]
        
        face = bm.faces.new([v1_curr, v2_curr, v2_next, v1_next])
        face.material_index = mat_idx
        
        v_curr = i / float(n - 1)
        v_next = (i + 1) / float(n - 1)
        for loop in face.loops:
            if loop.vert == v1_curr:
                loop[uv_layer].uv = Vector((u_range[0], 1.0 - v_curr))
            elif loop.vert == v2_curr:
                loop[uv_layer].uv = Vector((u_range[1], 1.0 - v_curr))
            elif loop.vert == v2_next:
                loop[uv_layer].uv = Vector((u_range[1], 1.0 - v_next))
            elif loop.vert == v1_next:
                loop[uv_layer].uv = Vector((u_range[0], 1.0 - v_next))

def add_flower(bm, center, normal, radius=0.030):
    u_axis = Vector((0, 0, 1)).cross(normal).normalized()
    v_axis = normal.cross(u_axis).normalized()
    num_p = 6
    v_c = bm.verts.new(center)
    for p in range(num_p):
        a1 = p * 2.0 * math.pi / num_p
        a2 = (p + 1) * 2.0 * math.pi / num_p
        am = (a1 + a2) * 0.5
        p1 = center + (u_axis * math.cos(a1) + v_axis * math.sin(a1)) * (radius * 0.35)
        pt = center + (u_axis * math.cos(am) + v_axis * math.sin(am)) * radius
        p2 = center + (u_axis * math.cos(a2) + v_axis * math.sin(a2)) * (radius * 0.35)
        v1 = bm.verts.new(p1)
        vt = bm.verts.new(pt)
        v2 = bm.verts.new(p2)
        f = bm.faces.new([v_c, v1, vt, v2])
        f.material_index = 2
        for loop in f.loops:
            loop[uv_layer].uv = Vector((0.75, 0.5))
            
    # Golden center pearl bead
    bead_r = radius * 0.35
    v_b = bm.verts.new(center + normal * (radius * 0.25))
    for p in range(num_p):
        a1 = p * 2.0 * math.pi / num_p
        a2 = (p + 1) * 2.0 * math.pi / num_p
        p1 = center + (u_axis * math.cos(a1) + v_axis * math.sin(a1)) * bead_r
        p2 = center + (u_axis * math.cos(a2) + v_axis * math.sin(a2)) * bead_r
        v1 = bm.verts.new(p1)
        v2 = bm.verts.new(p2)
        fb = bm.faces.new([v_b, v1, v2])
        fb.material_index = 2
        for loop in fb.loops:
            loop[uv_layer].uv = Vector((0.85, 0.85))

# 4.1 VOLUMETRIC HIGH-CROWN HAIR (High anime crown Z up to 1.765)
print('Constructing high-crown voluminous hair cap...')
num_crown_strands = 18
for c_i in range(num_crown_strands):
    ct = c_i / float(num_crown_strands - 1)
    c_ang = math.radians(-80.0 + 160.0 * ct)
    c_pts = []
    c_wids = []
    c_rad = 0.098
    for seg in range(12):
        st = seg / 11.0
        phi = math.radians(25.0 + 130.0 * st)
        px = c_rad * math.sin(c_ang) * (0.95 + 0.15 * math.sin(phi))
        py = -0.015 + c_rad * math.cos(phi) * 0.96
        pz = 1.66 + 0.105 * math.sin(phi)
        c_pts.append((px, py, pz))
        w = 0.038 * math.sin(st * math.pi * 0.85 + 0.15)
        c_wids.append(max(w, 0.003))
    create_ribbon_strand(bm_add, c_pts, c_wids, u_range=(0.15, 0.85), mat_idx=0)

# 4.2 ASTER'S LUSH LAYERED PARTED BANGS
print('Constructing Aster lush layered natural parted bangs...')

# Center lock (hangs right between eyes, Z down to 1.540)
center_pts = []
center_wids = []
for seg in range(12):
    st = seg / 11.0
    cx = 0.005 + 0.003 * math.sin(st * math.pi)
    cy = 0.065 + 0.040 * st + 0.012 * math.sin(st * math.pi)
    cz = 1.710 * (1.0 - st) + 1.540 * st
    center_pts.append((cx, cy, cz))
    w = 0.020 * math.sin(st * math.pi * 0.75 + 0.2) * (1.0 - 0.85 * st)
    center_wids.append(max(w, 0.0018))
create_ribbon_strand(bm_add, center_pts, center_wids, u_range=(0.2, 0.8), mat_idx=0)

# Left sweeping bangs (X < 0, sweeping gracefully over left brow with overlapping layers)
left_bang_configs = [
    (-0.024, -0.036, 1.542, 0.022),
    (-0.036, -0.050, 1.545, 0.024),
    (-0.048, -0.064, 1.548, 0.025),
    (-0.060, -0.078, 1.554, 0.025),
    (-0.072, -0.092, 1.562, 0.026),
    (-0.084, -0.104, 1.572, 0.025),
    (-0.094, -0.115, 1.585, 0.023),
]

for rx, tx, tz, wid in left_bang_configs:
    pts = []
    wids = []
    for seg in range(12):
        st = seg / 11.0
        cx = rx * (1.0 - st) + tx * st - 0.008 * math.sin(st * math.pi)
        cy = 0.062 * (1.0 - st) + 0.102 * st + 0.014 * math.sin(st * math.pi)
        cz = 1.712 * (1.0 - st) + tz * st
        pts.append((cx, cy, cz))
        w = wid * math.sin(st * math.pi * 0.65 + 0.2) * (1.0 - 0.82 * st)
        wids.append(max(w, 0.0020))
    create_ribbon_strand(bm_add, pts, wids, u_range=(0.1, 0.9), mat_idx=0)

# Right sweeping bangs (X > 0, parting window from 0.005 to 0.018, sweeping across right brow)
right_bang_configs = [
    (0.016, 0.024, 1.540, 0.021),
    (0.028, 0.038, 1.542, 0.023),
    (0.040, 0.052, 1.545, 0.025),
    (0.052, 0.066, 1.550, 0.025),
    (0.065, 0.080, 1.558, 0.026),
    (0.078, 0.094, 1.568, 0.025),
    (0.090, 0.106, 1.580, 0.024),
    (0.100, 0.116, 1.592, 0.022),
]

for rx, tx, tz, wid in right_bang_configs:
    pts = []
    wids = []
    for seg in range(12):
        st = seg / 11.0
        cx = rx * (1.0 - st) + tx * st + 0.008 * math.sin(st * math.pi)
        cy = 0.060 * (1.0 - st) + 0.102 * st + 0.014 * math.sin(st * math.pi)
        cz = 1.712 * (1.0 - st) + tz * st
        pts.append((cx, cy, cz))
        w = wid * math.sin(st * math.pi * 0.65 + 0.2) * (1.0 - 0.82 * st)
        wids.append(max(w, 0.0020))
    create_ribbon_strand(bm_add, pts, wids, u_range=(0.1, 0.9), mat_idx=0)

# 4.3 FACE-FRAMING SIDE LOCKS (Down past cheeks to upper chest Z=1.24)
print('Constructing face-framing side locks...')
for side in [-1.0, 1.0]:
    pts_side = []
    wids_side = []
    num_seg = 14
    for seg in range(num_seg):
        st = seg / float(num_seg - 1)
        cz = 1.63 * (1.0 - st) + 1.24 * st
        cx = side * (0.086 + 0.012 * math.sin(st * math.pi * 1.2) - 0.015 * (st ** 1.5))
        cy = 0.042 + 0.052 * st + 0.008 * math.sin(st * 2.5 * math.pi)
        pts_side.append((cx, cy, cz))
        w = 0.026 * (0.6 + 0.8 * math.sin(st * math.pi * 0.85)) * (1.0 - 0.80 * st)
        wids_side.append(max(w, 0.002))
    create_ribbon_strand(bm_add, pts_side, wids_side, u_range=(0.1, 0.9), mat_idx=0)

# 4.4 VOLUMETRIC CASCADING WAVY BACK HAIR (Past hips down to Z=0.74, flaring around waist bow)
print('Constructing voluminous cascading wavy back hair...')
num_tiers = 4
strands_per_tier = 22

for tier in range(num_tiers):
    tier_rad = 0.014 * tier
    tier_z = -0.015 * tier
    for s in range(strands_per_tier):
        t = s / float(strands_per_tier - 1)
        angle = math.radians(-150.0 + 300.0 * t)
        
        r_top = 0.094 + tier_rad
        x_top = r_top * math.sin(angle)
        y_top = -r_top * math.cos(angle) * 0.95 - 0.012
        z_top = 1.56 + tier_z
        
        pts_hair = []
        wids_hair = []
        num_seg = 14
        for seg in range(num_seg):
            st = seg / float(num_seg - 1)
            cur_z = z_top * (1.0 - st) + 0.74 * st
            spread = 1.0 + 1.45 * st + 0.55 * (st ** 2)
            cur_x = x_top * spread
            wave_x = 0.022 * math.sin(st * 3.8 * math.pi + angle * 1.6)
            wave_y = 0.015 * math.cos(st * 3.2 * math.pi + angle)
            
            cur_y = y_top * spread + wave_y
            if cur_y > -0.065:
                cur_y = -0.065
            if 0.95 <= cur_z <= 1.18:
                if abs(cur_x) < 0.065:
                    cur_x = math.copysign(0.065 + abs(cur_x) * 0.5, cur_x if abs(cur_x) > 0.001 else 1.0)
                cur_y = min(cur_y, -0.130 - 0.020 * tier)
                
            pts_hair.append((cur_x + wave_x, cur_y, cur_z))
            w = 0.038 * (0.6 + 0.9 * math.sin(st * math.pi * 0.85)) * (1.0 - 0.48 * st)
            wids_hair.append(max(w, 0.003))
            
        create_ribbon_strand(bm_add, pts_hair, wids_hair, u_range=(0.08, 0.92), mat_idx=0)

# 4.5 TWIN FLORAL CLIPS, RIBBONS & PEARL CHAINS
print('Constructing twin floral clips with streamers and pearl chains...')
clip_pos_l = Vector((0.116, 0.022, 1.585))
clip_norm_l = Vector((0.55, 0.78, 0.28)).normalized()
add_flower(bm_add, clip_pos_l, clip_norm_l, radius=0.030)
add_flower(bm_add, clip_pos_l + Vector((0.014, -0.012, 0.022)), clip_norm_l, radius=0.018)
add_flower(bm_add, clip_pos_l + Vector((0.010, -0.018, -0.020)), clip_norm_l, radius=0.016)

clip_pos_r = Vector((-0.116, 0.022, 1.585))
clip_norm_r = Vector((-0.55, 0.78, 0.28)).normalized()
add_flower(bm_add, clip_pos_r, clip_norm_r, radius=0.028)

for side in [-1.0, 1.0]:
    clip_pos = clip_pos_r if side < 0 else clip_pos_l
    for l_idx in range(2):
        l_sign = 1.0 if l_idx == 0 else -1.0
        loop_p = [
            clip_pos,
            clip_pos + Vector((side * 0.018, -0.022, 0.038 * l_sign)),
            clip_pos + Vector((side * 0.032, -0.012, 0.018 * l_sign)),
            clip_pos
        ]
        create_ribbon_strand(bm_add, loop_p, [0.008, 0.020, 0.018, 0.008], u_range=(0.1, 0.45), mat_idx=2)
    
    for r_i in range(2):
        r_pts = []
        r_wids = []
        off = 0.012 * (r_i - 0.5)
        for seg in range(12):
            st = seg / 11.0
            rz = 1.58 * (1.0 - st) + 1.26 * st
            rx = side * (0.116 + 0.014 * st) + off
            ry = 0.015 - 0.038 * st + 0.008 * math.sin(st * 3.2 * math.pi)
            r_pts.append((rx, ry, rz))
            w = 0.018 * (1.0 - 0.45 * st)
            r_wids.append(max(w, 0.002))
        create_ribbon_strand(bm_add, r_pts, r_wids, u_range=(0.1, 0.45), mat_idx=2)
        
    chain_pts = []
    for seg in range(9):
        st = seg / 8.0
        pz = 1.57 * (1.0 - st) + 1.34 * st
        px = side * (0.114 + 0.006 * st)
        py = 0.020 - 0.012 * st
        chain_pts.append((px, py, pz))
    create_ribbon_strand(bm_add, chain_pts, [0.006] * len(chain_pts), u_range=(0.8, 0.9), mat_idx=2)

# 4.6 BACK WAIST RIBBON BOW & STREAMERS
print('Constructing back waist ribbon bow...')
knot_pos = Vector((0.0, -0.125, 1.045))
for side in [-1.0, 1.0]:
    loop_pts = [
        knot_pos,
        knot_pos + Vector((side * 0.052, -0.026, 0.046)),
        knot_pos + Vector((side * 0.092, -0.030, 0.026)),
        knot_pos + Vector((side * 0.068, -0.020, -0.020)),
        knot_pos
    ]
    loop_wids = [0.018, 0.040, 0.046, 0.034, 0.018]
    create_ribbon_strand(bm_add, loop_pts, loop_wids, u_range=(0.1, 0.45), mat_idx=2)
    
    st_pts = []
    st_wids = []
    for seg in range(14):
        st = seg / 13.0
        sz = 1.04 * (1.0 - st) + 0.58 * st
        sx = side * (0.018 + 0.038 * st)
        sy = -0.130 - 0.028 * st + 0.010 * math.sin(st * 2.8 * math.pi)
        st_pts.append((sx, sy, sz))
        w = 0.030 * (1.0 - 0.35 * st)
        st_wids.append(max(w, 0.003))
    create_ribbon_strand(bm_add, st_pts, st_wids, u_range=(0.1, 0.45), mat_idx=2)

# 4.7 FRONT LEFT HIP FLOWER CORSAGE
print('Constructing front left hip floral corsage...')
corsage_pos = Vector((-0.118, 0.085, 1.045))
corsage_norm = Vector((-0.55, 0.75, 0.32)).normalized()
add_flower(bm_add, corsage_pos, corsage_norm, radius=0.030)

for l_idx in range(2):
    l_sign = 1.0 if l_idx == 0 else -1.0
    c_loop = [
        corsage_pos,
        corsage_pos + Vector((-0.024, 0.025, 0.034 * l_sign)),
        corsage_pos + Vector((-0.038, 0.015, 0.016 * l_sign)),
        corsage_pos
    ]
    create_ribbon_strand(bm_add, c_loop, [0.008, 0.020, 0.018, 0.008], u_range=(0.1, 0.45), mat_idx=2)

for r_i in range(2):
    c_pts = []
    c_wids = []
    off = 0.010 * (r_i - 0.5)
    for seg in range(14):
        st = seg / 13.0
        cz = 1.03 * (1.0 - st) + 0.68 * st
        cx = -0.118 - 0.030 * st + off
        cy = 0.088 + 0.022 * st + 0.008 * math.sin(st * 2.8 * math.pi)
        c_pts.append((cx, cy, cz))
        w = 0.020 * (1.0 - 0.38 * st)
        c_wids.append(max(w, 0.003))
    create_ribbon_strand(bm_add, c_pts, c_wids, u_range=(0.1, 0.45), mat_idx=2)

bm_add.to_mesh(mesh_new)
bm_add.free()
mesh_new.update()

# 5. SKINNING & WEIGHTS
vg_head = obj_new.vertex_groups.new(name='J_Bip_C_Head')
vg_spine = obj_new.vertex_groups.new(name='J_Bip_C_Spine')

for v in mesh_new.vertices:
    if v.co.z >= 1.25:
        vg_head.add([v.index], 1.0, 'REPLACE')
    elif v.co.z < 1.15:
        vg_spine.add([v.index], 1.0, 'REPLACE')
    else:
        t = (v.co.z - 1.15) / 0.10
        vg_head.add([v.index], t, 'REPLACE')
        vg_spine.add([v.index], 1.0 - t, 'REPLACE')

bpy.ops.object.select_all(action='DESELECT')
hair_obj.select_set(True)
obj_new.select_set(True)
bpy.context.view_layer.objects.active = hair_obj
bpy.ops.object.join()
print('Joined additions into Hair001.')

arm_mod = None
for m in hair_obj.modifiers:
    if m.type == 'ARMATURE':
        arm_mod = m
        break
if not arm_mod and armature:
    arm_mod = hair_obj.modifiers.new(name='Armature', type='ARMATURE')
    arm_mod.object = armature

# ==========================================================
# 6. RELOAD & ASSIGN MASTER TEXTURES TO BLENDER MATERIALS
# ==========================================================
print('Reloading master textures into Blender materials...')
tex_map = {
    'F00_000_00_EyeIris_00_EYE': 'aster_model_F00_000_EyeIris_00.png',
    'F00_000_00_EyeHighlight_00_EYE': 'aster_model_F00_000_EyeHighlight_00.png',
    'F00_000_00_EyeWhite_00_EYE': 'aster_model_F00_000_EyeWhite_00.png',
    'F00_000_00_FaceEyeline_00_FACE': 'aster_model_F00_000_FaceEyeline_00.png',
    'F00_000_00_FaceEyelash_00_FACE': 'aster_model_F00_000_FaceEyelash_00.png',
    'F00_000_00_FaceBrow_00_FACE': 'aster_model_F00_000_FaceBrow_00.png',
    'F00_000_00_Face_00_SKIN': 'aster_model_F00_000_Face_00.png',
    'F00_000_Hair_00_HAIR_01': 'aster_model_F00_000_Hair_00_01.png',
    'F00_000_Hair_00_HAIR_03': 'aster_model_F00_000_Hair_00_03.png',
    'F00_000_HairBack_00_HAIR': 'aster_model_F00_000_HairBack_00.png',
    'F00_002_01_Tops_01_CLOTH': 'aster_model_F00_002_Onepiece_01.png',
    'F00_002_01_Shoes_01_CLOTH': 'aster_model_F00_002_Shoes_01.png',
    'F00_002_02_Body_00_SKIN': 'aster_model_F00_002_Body_00.png',
}

for mat_name, file_name in tex_map.items():
    mat = bpy.data.materials.get(mat_name)
    file_path = os.path.join(models_dir, file_name)
    if mat and os.path.exists(file_path):
        img = bpy.data.images.load(filepath=file_path, check_existing=False)
        if mat.use_nodes:
            for n in mat.node_tree.nodes:
                if n.type == 'TEX_IMAGE':
                    n.image = img
                    print(f'Assigned {file_name} to {mat_name}')

# 7. EXPORT MASTER GLB
bpy.ops.object.select_all(action='DESELECT')
for o in [armature, body_obj, face_obj, hair_obj]:
    if o:
        o.select_set(True)

bpy.ops.export_scene.gltf(
    filepath=out_glb,
    use_selection=True,
    export_format='GLB',
    export_apply=False,
    export_yup=True,
    export_skins=True,
    export_morph=True,
    export_materials='EXPORT'
)

print(f'Master glTF exported successfully to: {out_glb}')
