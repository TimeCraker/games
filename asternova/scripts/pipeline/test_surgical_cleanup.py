# -*- coding: utf-8 -*-
"""AsterNova - Master Surgical Cleanup for Aster 56k Master Model.

Preserves the already-fixed legs and shoes, while cleanly healing:
1. Skirt: Removes all Arm/Hand weights and ALL Thigh weights from outer flared skirt (360 degrees).
2. Crotch: Anchors the sagittal center (|X| < 0.03) 100% to Pelvis to eliminate bridge stretching.
3. Arms: Frees cuffs and sleeves from Spine01/torso pinning, returning them to the arm chain.
4. Hair: Frees long back hair from torso pinning, locking it cleanly to Head.
5. Normalizes all affected vertices.
"""
import bpy
import math

def log(msg):
    print("[master_surgical_cleanup] " + str(msg), flush=True)

body = bpy.data.objects.get("Aster_Body")
arm = bpy.data.objects.get("Aster_Armature")
assert body and arm, "Missing Aster_Body or Aster_Armature!"

if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

mesh = body.data
v_count = len(mesh.vertices)
log(f"Processing Aster_Body: {v_count} vertices")

vg_map = {vg.name: vg for vg in body.vertex_groups}

ARM_BONES = {
    "L_Clavicle", "L_Upperarm", "L_Forearm", "L_Hand",
    "R_Clavicle", "R_Upperarm", "R_Forearm", "R_Hand",
    "L_UpperarmTwist01", "L_UpperarmTwist02", "L_ForearmTwist01", "L_ForearmTwist02",
    "R_UpperarmTwist01", "R_UpperarmTwist02", "R_ForearmTwist01", "R_ForearmTwist02"
}

TORSO_BONES = {"Pelvis", "Waist", "Spine01", "Spine02", "Hip"}

stats = {
    "skirt_arms_stripped": 0,
    "outer_skirt_thighs_stripped": 0,
    "crotch_anchored_to_pelvis": 0,
    "arm_cuffs_freed_from_torso": 0,
    "back_hair_freed": 0,
    "normalized": 0
}

for v in mesh.vertices:
    vi = v.index
    x, y, z = v.co.x, v.co.y, v.co.z
    r_xy = math.sqrt(x*x + y*y)
    
    # Read current weights
    w_dict = {}
    for g in v.groups:
        if g.group < len(body.vertex_groups):
            name = body.vertex_groups[g.group].name
            if g.weight > 1e-4:
                w_dict[name] = g.weight

    modified = False

    # -------------------------------------------------------------
    # 1. LONG BACK HAIR: Y < -0.045, Z in [0.75, 1.35], |X| < 0.28
    # -------------------------------------------------------------
    if y < -0.05 and 0.75 < z < 1.35 and abs(x) < 0.28:
        has_torso_w = any(b in TORSO_BONES for b in w_dict)
        has_head_w = "Head" in w_dict or "NeckTwist01" in w_dict
        if has_torso_w and (has_head_w or z > 0.85):
            for b in list(w_dict.keys()):
                if b in TORSO_BONES or "Thigh" in b or "Calf" in b:
                    del w_dict[b]
            w_dict["Head"] = w_dict.get("Head", 0.0) + 1.0
            modified = True
            stats["back_hair_freed"] += 1

    # -------------------------------------------------------------
    # 2. ARMS & CUFFS: |X| > 0.15, Z in [0.88, 1.35], not back hair
    # Free sleeve / wrist vertices from Spine01 / Pelvis / Waist
    # -------------------------------------------------------------
    if abs(x) > 0.15 and 0.88 < z < 1.35 and y > -0.045:
        # Right Arm
        if x > 0.15:
            torso_w = sum(w_dict.get(b, 0.0) for b in TORSO_BONES)
            if torso_w > 0.05:
                for b in list(w_dict.keys()):
                    if b in TORSO_BONES or b.startswith("L_"):
                        del w_dict[b]
                if not any(b.startswith("R_") for b in w_dict):
                    if x > 0.32 or z < 1.05:
                        w_dict["R_Hand"] = 1.0
                    elif x > 0.22:
                        w_dict["R_Forearm"] = 1.0
                    else:
                        w_dict["R_Upperarm"] = 1.0
                else:
                    best_arm = max((b for b in w_dict if b.startswith("R_")), key=lambda b: w_dict[b])
                    w_dict[best_arm] += torso_w
                modified = True
                stats["arm_cuffs_freed_from_torso"] += 1

        # Left Arm
        elif x < -0.15:
            torso_w = sum(w_dict.get(b, 0.0) for b in TORSO_BONES)
            if torso_w > 0.05:
                for b in list(w_dict.keys()):
                    if b in TORSO_BONES or b.startswith("R_"):
                        del w_dict[b]
                if not any(b.startswith("L_") for b in w_dict):
                    if x < -0.32 or z < 1.05:
                        w_dict["L_Hand"] = 1.0
                    elif x < -0.22:
                        w_dict["L_Forearm"] = 1.0
                    else:
                        w_dict["L_Upperarm"] = 1.0
                else:
                    best_arm = max((b for b in w_dict if b.startswith("L_")), key=lambda b: w_dict[b])
                    w_dict[best_arm] += torso_w
                modified = True
                stats["arm_cuffs_freed_from_torso"] += 1

    # -------------------------------------------------------------
    # 3. SKIRT: Z in [0.46, 0.88], not back hair
    # A) Strip ARM weights from entire skirt
    # B) Strip THIGH weights from outer flared skirt (360 deg)
    # -------------------------------------------------------------
    if 0.46 <= z <= 0.88 and y > -0.05:
        # A) Strip Arm weights
        arm_w = sum(w_dict.get(b, 0.0) for b in ARM_BONES)
        if arm_w > 0.001:
            for b in list(w_dict.keys()):
                if b in ARM_BONES:
                    del w_dict[b]
            target_torso = "Waist" if z > 0.80 else "Pelvis"
            w_dict[target_torso] = w_dict.get(target_torso, 0.0) + arm_w
            modified = True
            stats["skirt_arms_stripped"] += 1

        # B) Outer flared skirt: r_xy > 0.13 (or flared front y > 0.08 with r_xy > 0.11)
        # MUST NOT HAVE THIGH WEIGHTS!
        if r_xy > 0.13 or (y > 0.08 and r_xy > 0.11) or z > 0.75:
            thigh_w = w_dict.get("L_Thigh", 0.0) + w_dict.get("R_Thigh", 0.0)
            if thigh_w > 0.01:
                for b in ["L_Thigh", "R_Thigh"]:
                    if b in w_dict:
                        del w_dict[b]
                target_torso = "Waist" if z > 0.80 else "Pelvis"
                w_dict[target_torso] = w_dict.get(target_torso, 0.0) + thigh_w
                modified = True
                stats["outer_skirt_thighs_stripped"] += 1

    # -------------------------------------------------------------
    # 4. CROTCH CENTER: Sagittal plane |X| < 0.03, Z in [0.70, 0.88]
    # Anchor to Pelvis so moving legs don't create stretch bridge
    # -------------------------------------------------------------
    if abs(x) < 0.03 and 0.70 <= z <= 0.88:
        cross_thigh_w = w_dict.get("L_Thigh", 0.0) + w_dict.get("R_Thigh", 0.0)
        if cross_thigh_w > 0.05:
            for b in ["L_Thigh", "R_Thigh"]:
                if b in w_dict:
                    del w_dict[b]
            w_dict["Pelvis"] = w_dict.get("Pelvis", 0.0) + cross_thigh_w
            modified = True
            stats["crotch_anchored_to_pelvis"] += 1

    # -------------------------------------------------------------
    # Write back if modified
    # -------------------------------------------------------------
    if modified:
        sorted_inf = sorted(w_dict.items(), key=lambda item: -item[1])[:4]
        s = sum(w for _, w in sorted_inf)
        if s < 1e-6:
            sorted_inf = [("Pelvis", 1.0)]
            s = 1.0

        for g in list(v.groups):
            body.vertex_groups[g.group].remove([vi])

        for bname, raw_w in sorted_inf:
            norm_w = raw_w / s
            vg_map[bname].add([vi], norm_w, 'REPLACE')
        stats["normalized"] += 1

log("Master cleanup stats:")
for k, val in stats.items():
    log(f"  {k}: {val}")

mesh.update()
log("Mesh updated successfully!")
