# -*- coding: utf-8 -*-
"""Master Skinning Perfection V2 for Aster (56,437 vertices).

Mathematically rigorous 3D bone projection, continuous Hermite transitions,
and 100% anatomical isolation of Skirt, Hair, Arms, Legs, and Torso.
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector

def log(msg):
    print("[skinning_v2] " + str(msg), flush=True)

body = bpy.data.objects.get("Aster_Body")
arm = bpy.data.objects.get("Aster_Armature")
assert body and arm, "Missing Aster_Body or Aster_Armature!"

if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

mesh = body.data
v_count = len(mesh.vertices)
log(f"Processing Aster_Body: {v_count} vertices")

vg_map = {vg.name: vg for vg in body.vertex_groups}

def smoothstep(e0, e1, x):
    if x <= e0: return 0.0
    if x >= e1: return 1.0
    t = (x - e0) / (e1 - e0)
    return t * t * (3.0 - 2.0 * t)

def dist_to_segment(p, a, b):
    ab = b - a
    lsq = ab.length_squared
    if lsq < 1e-8: return (p - a).length
    t = max(0.0, min(1.0, (p - a).dot(ab) / lsq))
    return (p - (a + t * ab)).length

def proj_along_segment(p, a, b):
    ab = b - a
    lsq = ab.length_squared
    if lsq < 1e-8: return 0.0
    return (p - a).dot(ab) / lsq

# 1. Bone segments in local coordinates
bones = arm.data.bones
l_thigh_h = bones['L_Thigh'].head_local
l_thigh_t = bones['L_Thigh'].tail_local
r_thigh_h = bones['R_Thigh'].head_local
r_thigh_t = bones['R_Thigh'].tail_local

l_calf_h = bones['L_Calf'].head_local
l_calf_t = bones['L_Calf'].tail_local
r_calf_h = bones['R_Calf'].head_local
r_calf_t = bones['R_Calf'].tail_local

l_clav_h = bones['L_Clavicle'].head_local
l_clav_t = bones['L_Clavicle'].tail_local
l_upper_h = bones['L_Upperarm'].head_local
l_upper_t = bones['L_Upperarm'].tail_local
l_fore_h = bones['L_Forearm'].head_local
l_fore_t = bones['L_Forearm'].tail_local
l_hand_h = bones['L_Hand'].head_local
# Fix left hand direction to point outward towards fingertips
l_hand_t = Vector((-0.499, -0.048, 0.831))

r_clav_h = bones['R_Clavicle'].head_local
r_clav_t = bones['R_Clavicle'].tail_local
r_upper_h = bones['R_Upperarm'].head_local
r_upper_t = bones['R_Upperarm'].tail_local
r_fore_h = bones['R_Forearm'].head_local
r_fore_t = bones['R_Forearm'].tail_local
r_hand_h = bones['R_Hand'].head_local
r_hand_t = bones['R_Hand'].tail_local

# 2. Identify Thigh/Leg vertices via flood fill from knees
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()

l_seed = [v for v in bm.verts if 0.44 <= v.co.z <= 0.48 and v.co.x < -0.01]
r_seed = [v for v in bm.verts if 0.44 <= v.co.z <= 0.48 and v.co.x > 0.01]

def flood_fill_legs(seeds, max_z=0.88):
    visited = set(v.index for v in seeds)
    stack = list(seeds)
    while stack:
        cur = stack.pop()
        for e in cur.link_edges:
            nxt = e.other_vert(cur)
            if nxt.index not in visited and nxt.co.z <= max_z:
                # Keep within thigh bounds (not leaping to skirt)
                if abs(nxt.co.y) < 0.10:
                    visited.add(nxt.index)
                    stack.append(nxt)
    return visited

l_leg_indices = flood_fill_legs(l_seed)
r_leg_indices = flood_fill_legs(r_seed)
bm.free()

log(f"Leg flood fill identified: Left leg {len(l_leg_indices)} verts, Right leg {len(r_leg_indices)} verts")

# Also add cylinder check for any floating thigh verts
def is_thigh_vert(p, is_left):
    if is_left:
        d = dist_to_segment(p, l_thigh_h, l_thigh_t)
        return (d < 0.052 and -0.06 < p.y < 0.05 and p.x < -0.01)
    else:
        d = dist_to_segment(p, r_thigh_h, r_thigh_t)
        return (d < 0.052 and -0.06 < p.y < 0.05 and p.x > 0.01)

stats = {
    "shoes_socks_calves_kept": 0,
    "hair_head": 0,
    "neck": 0,
    "torso": 0,
    "right_arm": 0,
    "left_arm": 0,
    "thighs": 0,
    "skirt": 0
}

all_new_weights = []

for idx, v in enumerate(mesh.vertices):
    p = v.co
    x, y, z = p.x, p.y, p.z
    r_xy = math.sqrt(x*x + y*y)

    w_curr = {}
    for g in v.groups:
        if g.group < len(body.vertex_groups):
            bname = body.vertex_groups[g.group].name
            if g.weight > 1e-4:
                w_curr[bname] = g.weight

    w_new = {}

    # =========================================================================
    # 1. PRESERVE LOWER LEGS, SOCKS & SHOES (Z < 0.45)
    # User confirmed: "腿是没问题了" - 100% keep verified pristine weights!
    # =========================================================================
    if z < 0.45:
        # Check if it's the skirt hem ruffle that drops slightly below 0.45 at outer perimeter
        if r_xy > 0.16 and (y < -0.06 or y > 0.08):
            w_new['Pelvis'] = 1.0
            stats["skirt"] += 1
        else:
            w_new = dict(w_curr)
            stats["shoes_socks_calves_kept"] += 1

    # =========================================================================
    # 2. HEAD & ALL HAIR
    # Long flowing back hair, head accessories, face, bangs, side strands
    # =========================================================================
    elif (z >= 1.34 and abs(x) < 0.32) or (y < -0.065 and z >= 0.65 and abs(x) <= 0.30) or (z >= 1.22 and abs(x) > 0.08 and abs(x) <= 0.28 and y < 0.05):
        # Neck center cylinder transition
        if abs(x) < 0.055 and abs(y) < 0.05 and 1.25 <= z <= 1.34:
            t = smoothstep(1.25, 1.34, z)
            w_new['Head'] = t
            w_new['NeckTwist01'] = 1.0 - t
            stats["neck"] += 1
        else:
            w_new['Head'] = 1.0
            stats["hair_head"] += 1

    # =========================================================================
    # 3. RIGHT ARM & SLEEVE & HAND (X > 0.12, Z >= 0.85, Y >= -0.065)
    # Continuous Hermite weighting along 3D bone chain
    # =========================================================================
    elif x > 0.12 and z >= 0.85 and y >= -0.065:
        t_up = proj_along_segment(p, r_upper_h, r_upper_t)
        t_fo = proj_along_segment(p, r_fore_h, r_fore_t)
        t_ha = proj_along_segment(p, r_hand_h, r_hand_t)
        
        # Shoulder / Clavicle transition
        if t_up < 0.15:
            u = smoothstep(-0.20, 0.15, t_up)
            w_new['R_Clavicle'] = 1.0 - u
            w_new['R_Upperarm'] = u
        # Bicep / Upperarm
        elif t_up < 0.80:
            w_new['R_Upperarm'] = 1.0
        # Elbow transition (blend between Upperarm and Forearm)
        elif t_up < 1.05 and t_fo < 0.25:
            # Normalized elbow parameter: t_up from 0.80 to 1.05
            u = smoothstep(0.80, 1.05, t_up)
            w_new['R_Upperarm'] = 1.0 - u
            w_new['R_Forearm'] = u
        # Forearm
        elif t_fo < 0.80:
            w_new['R_Forearm'] = 1.0
        # Wrist transition (blend between Forearm and Hand)
        elif t_fo < 1.10 and t_ha < 0.20:
            u = smoothstep(0.80, 1.05, t_fo)
            w_new['R_Forearm'] = 1.0 - u
            w_new['R_Hand'] = u
        # Hand & Fingers
        else:
            w_new['R_Hand'] = 1.0
            
        stats["right_arm"] += 1

    # =========================================================================
    # 4. LEFT ARM & SLEEVE & HAND (X < -0.12, Z >= 0.85, Y >= -0.065)
    # Continuous Hermite weighting along 3D bone chain
    # =========================================================================
    elif x < -0.12 and z >= 0.85 and y >= -0.065:
        t_up = proj_along_segment(p, l_upper_h, l_upper_t)
        t_fo = proj_along_segment(p, l_fore_h, l_fore_t)
        t_ha = proj_along_segment(p, l_hand_h, l_hand_t)
        
        # Shoulder / Clavicle transition
        if t_up < 0.15:
            u = smoothstep(-0.20, 0.15, t_up)
            w_new['L_Clavicle'] = 1.0 - u
            w_new['L_Upperarm'] = u
        # Bicep / Upperarm
        elif t_up < 0.80:
            w_new['L_Upperarm'] = 1.0
        # Elbow transition (blend between Upperarm and Forearm)
        elif t_up < 1.05 and t_fo < 0.25:
            u = smoothstep(0.80, 1.05, t_up)
            w_new['L_Upperarm'] = 1.0 - u
            w_new['L_Forearm'] = u
        # Forearm
        elif t_fo < 0.80:
            w_new['L_Forearm'] = 1.0
        # Wrist transition (blend between Forearm and Hand)
        elif t_fo < 1.10 and t_ha < 0.20:
            u = smoothstep(0.80, 1.05, t_fo)
            w_new['L_Forearm'] = 1.0 - u
            w_new['L_Hand'] = u
        # Hand & Fingers
        else:
            w_new['L_Hand'] = 1.0
            
        stats["left_arm"] += 1

    # =========================================================================
    # 5. THIGHS (0.45 <= Z <= 0.88)
    # Identified by flood fill from knees OR tight thigh cylinder
    # =========================================================================
    elif 0.45 <= z <= 0.88 and (
        idx in l_leg_indices or idx in r_leg_indices or
        is_thigh_vert(p, True) or is_thigh_vert(p, False)
    ):
        is_left = (idx in l_leg_indices) or is_thigh_vert(p, True) or (x < 0.0)
        target_thigh = 'L_Thigh' if is_left else 'R_Thigh'
        target_calf = 'L_Calf' if is_left else 'R_Calf'
        
        # Crotch center (|X| <= 0.015, Z >= 0.78)
        if abs(x) <= 0.015 and z >= 0.78:
            w_new['Pelvis'] = 1.0
        # Upper thigh blend into Pelvis
        elif z > 0.80:
            u = smoothstep(0.80, 0.88, z)
            w_new[target_thigh] = 1.0 - u
            w_new['Pelvis'] = u
        # Knee blend from Calf to Thigh
        elif z < 0.53:
            u = smoothstep(0.45, 0.53, z)
            w_new[target_calf] = 1.0 - u
            w_new[target_thigh] = u
        else:
            w_new[target_thigh] = 1.0
            
        stats["thighs"] += 1

    # =========================================================================
    # 6. THE SKIRT & RUFFLES (Z in [0.40, 0.88], not thigh)
    # Driven 100% by Pelvis, smoothly blending into Waist at top waistband
    # =========================================================================
    elif 0.40 <= z <= 0.88:
        if z > 0.82:
            u = smoothstep(0.82, 0.88, z)
            w_new['Pelvis'] = 1.0 - 0.35 * u
            w_new['Waist'] = 0.35 * u
        else:
            w_new['Pelvis'] = 1.0
        stats["skirt"] += 1

    # =========================================================================
    # 7. TORSO (Z in [0.86, 1.34], |X| <= 0.16)
    # Corset, Blouse, Chest, Clavicle roots
    # =========================================================================
    elif 0.86 <= z <= 1.34:
        if z >= 1.25:
            u = smoothstep(1.25, 1.34, z)
            w_new['Spine02'] = 1.0 - 0.5 * u
            w_new['NeckTwist01'] = 0.5 * u
        elif z >= 1.13:
            u = smoothstep(1.13, 1.25, z)
            w_new['Spine01'] = 1.0 - u
            w_new['Spine02'] = u
        elif z >= 0.97:
            u = smoothstep(0.97, 1.13, z)
            w_new['Waist'] = 1.0 - u
            w_new['Spine01'] = u
        else:
            u = smoothstep(0.86, 0.97, z)
            w_new['Pelvis'] = 1.0 - u
            w_new['Waist'] = u
        stats["torso"] += 1

    # =========================================================================
    # 8. FALLBACK
    # =========================================================================
    else:
        if z > 1.30: w_new['Head'] = 1.0
        elif z > 0.95: w_new['Spine01'] = 1.0
        else: w_new['Pelvis'] = 1.0

    all_new_weights.append(w_new)

# Apply normalized weights to Aster_Body
log("Applying master weights to Aster_Body...")
for i, w_dict in enumerate(all_new_weights):
    s = sum(w_dict.values())
    if s < 1e-6:
        w_dict = {'Pelvis': 1.0}
        s = 1.0
    v = mesh.vertices[i]
    for g in list(v.groups):
        body.vertex_groups[g.group].remove([i])
    for bname, raw_w in w_dict.items():
        norm_w = raw_w / s
        if bname in vg_map and norm_w > 1e-4:
            vg_map[bname].add([i], norm_w, 'REPLACE')

mesh.update()
log("Master Skinning V2 successfully applied!")
for k, v in stats.items():
    log(f"  {k}: {v}")
