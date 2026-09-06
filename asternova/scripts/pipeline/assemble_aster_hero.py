# -*- coding: utf-8 -*-
"""AsterNova - Assemble Aster Hero: scale calibration, weapon sockets, katana mounting,
hair normal smoothing, .blend/.glb export, and 2K studio turnaround renders.

Run:  blender.exe -b --factory-startup -P assemble_aster_hero.py
Inputs : art/models/raw_ai_sculpt/aster_raw_sculpt.glb   (1.0m Tripo humanoid, 41 bones,
         contains a junk 'Icosphere' helper mesh that we drop)
         art/models/weapons/aster_katana/aster_katana.glb (koiguchi origin, blade -Z / handle +Z)
Outputs: art/models/aster_assembled.blend / .glb
         art/render_previews/characters/aster/aster_assembly_{front,three_quarter,back}.png
"""
import bpy, os, math, json
from mathutils import Vector, Matrix

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
RAW_GLB = os.path.join(REPO, r"art\models\raw_ai_sculpt\aster_raw_sculpt.glb")
KATANA_GLB = os.path.join(REPO, r"art\models\weapons\aster_katana\aster_katana.glb")
OUT_BLEND = os.path.join(REPO, r"art\models\aster_assembled.blend")
OUT_GLB = os.path.join(REPO, r"art\models\aster_assembled.glb")
PREVIEW_DIR = os.path.join(REPO, r"art\render_previews\characters\aster")

TARGET_HEIGHT = 1.650  # meters
REPORT = {}


def log(msg):
    print("[assemble] " + str(msg), flush=True)


# ----------------------------------------------------------------------------
# 0. Clean scene
# ----------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=False)
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


def world_bbox(obj):
    """Exact world-space bbox from evaluated mesh vertices (armature-deform aware)."""
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    mw = ev.matrix_world
    xs, ys, zs = [], [], []
    for v in ev.data.vertices:
        w = mw @ v.co
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def select_only(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


# ----------------------------------------------------------------------------
# 1. Import raw sculpt, keep the real skinned mesh, drop junk helpers
# ----------------------------------------------------------------------------
before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=RAW_GLB)
new_objs = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before]
arm = next(o for o in new_objs if o.type == 'ARMATURE')
meshes = [o for o in new_objs if o.type == 'MESH']
body = max(meshes, key=lambda o: len(o.data.vertices))
for junk in meshes:
    if junk is not body:
        log(f"dropping junk mesh {junk.name} ({len(junk.data.vertices)} verts)")
        bpy.data.objects.remove(junk, do_unlink=True)
arm.name = "Aster_Armature"
body.name = "Aster_Body"
log(f"imported: armature={arm.name} mesh={body.name} verts={len(body.data.vertices)} "
    f"arm_matrix_rot={[round(math.degrees(a),1) for a in arm.matrix_world.to_euler()]}")

bone_names = [b.name for b in arm.data.bones]
assert "R_Hand" in bone_names and "Pelvis" in bone_names, f"missing bones: {bone_names}"
REPORT["bone_count"] = len(bone_names)

# ----------------------------------------------------------------------------
# 2. Scale to 1.650m (uniform, keeps parenting & weights)
# ----------------------------------------------------------------------------
mn, mx = world_bbox(body)
raw_h = mx[2] - mn[2]
s = TARGET_HEIGHT / raw_h
log(f"raw height={raw_h:.5f}m  scale factor={s:.5f}")
S = Matrix.Scale(s, 4)
for o in (arm, body):
    o.matrix_world = S @ o.matrix_world
select_only([arm, body])
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
log(f"post-apply armature matrix euler(deg)={[round(math.degrees(a),2) for a in arm.matrix_world.to_euler()]}")

# ----------------------------------------------------------------------------
# 3. Ground Z=0 and center XY on (0,0)  (measure the deformed mesh, move armature)
# ----------------------------------------------------------------------------
mn, mx = world_bbox(body)
delta = Vector((-(mn[0] + mx[0]) / 2.0, -(mn[1] + mx[1]) / 2.0, -mn[2]))
arm.location = arm.location + delta
bpy.context.view_layer.update()
mn, mx = world_bbox(body)
resid = Vector((-(mn[0] + mx[0]) / 2.0, -(mn[1] + mx[1]) / 2.0, -mn[2]))
if resid.length > 1e-6:
    body.location = body.location + resid
    bpy.context.view_layer.update()
    mn, mx = world_bbox(body)

height = mx[2] - mn[2]
log(f"calibrated: height={height:.5f} zmin={mn[2]:.6f} center_xy=({(mn[0]+mx[0])/2:.6f},{(mn[1]+mx[1])/2:.6f})")
REPORT["height_m"] = round(height, 5)
REPORT["scale_factor"] = round(s, 5)
assert abs(height - TARGET_HEIGHT) < 0.001, "height calibration failed"

# Export-facing convention: rotate the whole assembly +90 deg about Z so that the
# character (raw facing +X in Blender) faces +Y in Blender == -Z in glTF/Godot,
# matching the turnaround stage cameras and Godot's forward convention.
Rz = Matrix.Rotation(math.radians(90.0), 4, 'Z')
for o in (arm, body):
    o.matrix_world = Rz @ o.matrix_world
select_only([arm, body])
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.view_layer.update()
mn, mx = world_bbox(body)
log(f"post-rotation: height={mx[2]-mn[2]:.5f} center_xy=({(mn[0]+mx[0])/2:.6f},{(mn[1]+mx[1])/2:.6f})")

# ----------------------------------------------------------------------------
# 4. Facing from skinned vertex groups (bones may sit in a rotated/scaled space;
#    the WEIGHTS give true visual positions)
# ----------------------------------------------------------------------------
def weighted_group_center(group_name):
    idx = body.vertex_groups.get(group_name).index if body.vertex_groups.get(group_name) else None
    if idx is None:
        return None
    acc = Vector((0, 0, 0)); wsum = 0.0
    for v in body.data.vertices:
        w = 0.0
        for g in v.groups:
            if g.group == idx:
                w = g.weight
                break
        if w > 0.05:
            acc += body.matrix_world @ v.co * w
            wsum += w
    return acc / wsum if wsum > 0 else None


c_r = weighted_group_center("R_Hand")
c_l = weighted_group_center("L_Hand")
log(f"visual hand centers: R={tuple(round(v,4) for v in c_r)} L={tuple(round(v,4) for v in c_l)}")
l2r = (c_r - c_l); l2r.z = 0.0
l2r.normalize()
forward = Vector((0, 0, 1)).cross(l2r).normalized()   # up x (R-L) = facing
right_dir = l2r
left_dir = -l2r
log(f"derived facing forward={tuple(round(v,4) for v in forward)} right={tuple(round(v,4) for v in right_dir)}")

# ----------------------------------------------------------------------------
# 5. Weapon sockets (edit bones; all math in world space)
# ----------------------------------------------------------------------------
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
arm_mw_inv = arm.matrix_world.inverted()


def make_socket(name, parent_name, head_w, tail_w):
    b = eb.new(name)
    b.head = arm_mw_inv @ head_w
    b.tail = arm_mw_inv @ tail_w
    b.parent = eb[parent_name]
    b.use_connect = False
    b.roll = 0.0
    log(f"socket {name}: parent={parent_name} head_w=({head_w.x:.4f},{head_w.y:.4f},{head_w.z:.4f})")
    return b


hand_w = arm.matrix_world @ eb["R_Hand"].head
hand_tail_w = arm.matrix_world @ eb["R_Hand"].tail
palm = hand_w.lerp(hand_tail_w, 0.5)
# visual check: palm should be near the weighted R_Hand center
log(f"palm(bone)={tuple(round(v,4) for v in palm)} vs palm(weights)={tuple(round(v,4) for v in c_r)}")

blade_len = 0.685   # raw katana blade length (m) - weapon is NOT rescaled


def blade_direction(a):
    d = (right_dir * a + forward * a + Vector((0, 0, -1)) * 1.15)
    d.normalize()
    return d


a = 0.8
bd = blade_direction(a)
while palm.z - blade_len * (-bd.z) < 0.02 and a < 2.5:
    a += 0.15
    bd = blade_direction(a)
handle_dir = -bd


def frame_from_z(zdir):
    """4x4 whose local +Z axis maps to zdir (X/Y are any clean perpendicular pair)."""
    zc = zdir.normalized()
    xc = zc.cross(Vector((0, 0, 1)))
    if xc.length < 1e-4:
        xc = zc.cross(Vector((0, 1, 0)))
    xc.normalize()
    yc = zc.cross(xc).normalized()
    return Matrix((xc, yc, zc)).transposed().to_4x4()


M_hand = frame_from_z(handle_dir)
M_hand.translation = palm
make_socket("Hand_R_Weapon_Socket", "R_Hand", palm, palm + handle_dir * 0.12)

pelvis_head_w = arm.matrix_world @ eb["Pelvis"].head
tilt = math.radians(15.0)
hang = (left_dir * math.sin(tilt) + Vector((0, 0, -1)) * math.cos(tilt)).normalized()
kata_len = 0.72  # raw katana overall length (m)
if pelvis_head_w.z - kata_len * (-hang.z) < 0.02:
    tilt = math.radians(45.0)
    hang = (left_dir * math.sin(tilt) + Vector((0, 0, -1)) * math.cos(tilt)).normalized()
    log("scabbard tilt increased to 45deg to keep tip above floor")
scab_head = pelvis_head_w + left_dir * 0.105 - forward * 0.02
M_scab = frame_from_z(-hang)   # scabbard body extends local -Z -> align with hang
M_scab.translation = scab_head
make_socket("Pelvis_L_Scabbard_Socket", "Pelvis", scab_head, scab_head + hang * 0.12)
REPORT["sockets"] = ["Hand_R_Weapon_Socket", "Pelvis_L_Scabbard_Socket"]

# ----------------------------------------------------------------------------
# 6. Import katana, mount into sockets (empirically corrected bone parenting)
# ----------------------------------------------------------------------------
before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=KATANA_GLB)
kat_objs = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before]
blade = next(o for o in kat_objs if "Blade" in o.name)
scabbard = next(o for o in kat_objs if "Scabbard" in o.name)
blade.name = "Katana_Blade"
scabbard.name = "Katana_Scabbard"
log(f"katana imported: {blade.name}, {scabbard.name}")
for o in kat_objs:
    if o.type == 'EMPTY':
        bpy.data.objects.remove(o, do_unlink=True)
# bake the glTF importer's Y-up->Z-up object rotation into mesh data so a plain
# identity basis after bone-mounting keeps the authored orientation
select_only([blade, scabbard])
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
log("katana object rotation baked into mesh data")

# The authored saya (scabbard body) ships with inward-pointing normals; EEVEE's
# double-sided shading hides it, but single-sided NPR pipelines render it black.
# Deterministically flip faces whose normals face the long axis (radial test).
import bmesh

saya_idx = next(i for i, m in enumerate(scabbard.data.materials)
                if m and "Saya" in m.name)
bm = bmesh.new()
bm.from_mesh(scabbard.data)
saya_faces = [f for f in bm.faces if f.material_index == saya_idx]
axis = Vector((0.0, 0.0, 1.0))
inward = outward = 0
for f in saya_faces:
    radial = f.calc_center_median()
    radial -= axis * radial.dot(axis)
    if radial.length < 1e-9:
        continue
    if f.normal.dot(radial.normalized()) < 0:
        inward += 1
    else:
        outward += 1
if inward > outward:
    bmesh.ops.reverse_faces(bm, faces=saya_faces)
    log(f"scabbard saya normals flipped (inward={inward} outward={outward})")
else:
    log(f"scabbard saya normals already outward (inward={inward} outward={outward})")
bm.to_mesh(scabbard.data)
bm.free()
scabbard.data.update()


def mount_to_bone(obj, bone_name, desired_world):
    """Parent to bone; Blender's bone-parent evaluation frame is not documented as
    matching Bone.matrix_local, so we measure once and correct parent_inverse exactly."""
    obj.parent = arm
    obj.parent_type = 'BONE'
    obj.parent_bone = bone_name
    bone_world = arm.matrix_world @ arm.data.bones[bone_name].matrix_local
    pi = bone_world.inverted() @ desired_world
    obj.matrix_parent_inverse = pi
    obj.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    actual = obj.matrix_world.copy()
    # evaluation frame F satisfies actual = F @ pi ; solve pi' = F^-1 @ desired
    f = actual @ pi.inverted()
    obj.matrix_parent_inverse = f.inverted() @ desired_world
    obj.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    err = (obj.matrix_world.translation - desired_world.translation).length
    log(f"mounted {obj.name} on {bone_name}: residual err={err:.6f} m")
    return err


e1 = mount_to_bone(blade, "Hand_R_Weapon_Socket", M_hand)
e2 = mount_to_bone(scabbard, "Pelvis_L_Scabbard_Socket", M_scab)
REPORT["socket_err_hand_m"] = round(e1, 6)
REPORT["socket_err_scabbard_m"] = round(e2, 6)

bm_n, bm_x = world_bbox(blade)
sm_n, sm_x = world_bbox(scabbard)
log(f"blade world bbox z=[{bm_n[2]:.4f},{bm_x[2]:.4f}] floor clearance={bm_n[2]:.4f}")
log(f"scabbard world bbox z=[{sm_n[2]:.4f},{sm_x[2]:.4f}] floor clearance={sm_n[2]:.4f}")
REPORT["blade_floor_clearance_m"] = round(bm_n[2], 4)
REPORT["scabbard_floor_clearance_m"] = round(sm_n[2], 4)

# ----------------------------------------------------------------------------
# 7. Hair / head normal smoothing (smooth + 60deg auto angle on the body mesh)
# ----------------------------------------------------------------------------
select_only([body])
bpy.ops.object.shade_smooth()
done_smooth = "shade_smooth"
try:
    bpy.ops.object.shade_auto_smooth(angle=math.radians(60))
    done_smooth = "shade_auto_smooth(60deg)"
except Exception:
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(60))
        done_smooth = "shade_smooth_by_angle(60deg)"
    except Exception:
        log("auto-smooth op unavailable; plain shade_smooth kept")
log(f"normals smoothed via {done_smooth}")
REPORT["normal_smoothing"] = done_smooth

# ----------------------------------------------------------------------------
# 8. Poly stats
# ----------------------------------------------------------------------------
deps = bpy.context.evaluated_depsgraph_get()
ev_body = body.evaluated_get(deps)
polys = len(ev_body.data.polygons)
tris = sum(max(1, len(p.vertices) - 2) for p in ev_body.data.polygons)
ev_bl = blade.evaluated_get(deps)
ev_sc = scabbard.evaluated_get(deps)
kat_polys = len(ev_bl.data.polygons) + len(ev_sc.data.polygons)
kat_tris = sum(max(1, len(p.vertices) - 2) for p in ev_bl.data.polygons) + \
    sum(max(1, len(p.vertices) - 2) for p in ev_sc.data.polygons)
log(f"body polys={polys} tris={tris}; katana polys={kat_polys} tris={kat_tris}")
REPORT["body_polys"] = polys
REPORT["body_tris"] = tris
REPORT["katana_polys"] = kat_polys
REPORT["katana_tris"] = kat_tris

# ----------------------------------------------------------------------------
# 9. Save .blend and export .glb (kwargs adapted to this Blender version)
# ----------------------------------------------------------------------------
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
log(f"saved {OUT_BLEND}")

exp_props = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
kwargs = {"filepath": OUT_GLB, "export_format": 'GLB', "export_apply": True,
          "export_materials": 'EXPORT', "export_yup": True}
if "export_selected_objects" in exp_props:
    kwargs["export_selected_objects"] = True
elif "use_selection" in exp_props:
    kwargs["use_selection"] = True
for k, v in (("export_animations", False), ("export_skins", True)):
    if k in exp_props:
        kwargs[k] = v
select_only([arm, body, blade, scabbard])
bpy.ops.export_scene.gltf(**kwargs)
log(f"exported {OUT_GLB} ({os.path.getsize(OUT_GLB)} bytes)")
REPORT["export_kwargs"] = sorted(kwargs.keys())

# ----------------------------------------------------------------------------
# 10. 2K studio renders (front / 3-4 / back), camera derived from facing
# ----------------------------------------------------------------------------
os.makedirs(PREVIEW_DIR, exist_ok=True)
scene = bpy.context.scene


def pick_eevee():
    for eid in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            scene.render.engine = eid
            return eid
        except Exception:
            continue
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    return 'CYCLES'


engine = pick_eevee()
log(f"render engine: {engine}")
scene.render.resolution_x = 2048
scene.render.resolution_y = 2048
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
if engine.startswith('BLENDER_EEVEE'):
    for attr, val in (("taa_render_samples", 64),):
        try:
            setattr(scene.eevee, attr, val)
        except Exception:
            pass

world = bpy.data.worlds.new("StudioWorld")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.93, 0.96, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.85
scene.world = world


def add_area_light(name, loc, energy, size, aim_z=0.9):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    scene.collection.objects.link(lo)
    aim = bpy.data.objects.new(name + "_Aim", None)
    aim.location = (0, 0, aim_z)
    scene.collection.objects.link(aim)
    c = lo.constraints.new('TRACK_TO')
    c.target = aim
    return lo


fwd = forward
rgt = right_dir
add_area_light("Key", fwd * 1.8 + rgt * 1.6 + Vector((0, 0, 2.4)), 130, 2.2)
add_area_light("Fill", fwd * 1.6 - rgt * 1.8 + Vector((0, 0, 1.6)), 50, 2.8)
add_area_light("Rim", -fwd * 2.2 + Vector((0, 0, 2.0)), 90, 1.8)

cam_data = bpy.data.cameras.new("ReviewCam")
cam_data.lens = 85
cam_data.clip_start = 0.05
cam_data.clip_end = 60
cam = bpy.data.objects.new("ReviewCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
track = cam.constraints.new('TRACK_TO')
tgt = bpy.data.objects.new("TrackTarget", None)
tgt.location = Vector((0, 0, 0.825))
scene.collection.objects.link(tgt)
track.target = tgt

# frame on everything (body + mounted katana)
b_n, b_x = world_bbox(body)
allmn = [min(b_n[i], bm_n[i], sm_n[i]) for i in range(3)]
allmx = [max(b_x[i], bm_x[i], sm_x[i]) for i in range(3)]
mid_z = (allmn[2] + allmx[2]) / 2.0
tgt.location = Vector((0, 0, mid_z))
half_h = (allmx[2] - allmn[2]) / 2.0 + 0.05
half_w = max(allmx[0] - allmn[0], allmx[1] - allmn[1]) / 2.0 + 0.08
tan_h = math.tan(math.atan(18.0 / 85.0))  # square render -> sensor 36mm both axes
dist = max(half_h, half_w) / tan_h * 1.06
log(f"studio camera distance={dist:.3f} mid_z={mid_z:.3f} half_h={half_h:.3f}")


def render_view(azimuth_deg, out_name):
    a = math.radians(azimuth_deg)
    dirv = forward * math.cos(a) + right_dir * math.sin(a)
    cam.location = Vector((dirv.x * dist, dirv.y * dist, mid_z + dist * 0.04))
    scene.render.filepath = os.path.join(PREVIEW_DIR, out_name)
    bpy.ops.render.render(write_still=True)
    log(f"rendered {scene.render.filepath}")


render_view(0, "aster_assembly_front.png")        # camera on facing side
render_view(40, "aster_assembly_three_quarter.png")
render_view(180, "aster_assembly_back.png")

REPORT["renders"] = ["aster_assembly_front.png", "aster_assembly_three_quarter.png",
                     "aster_assembly_back.png"]
REPORT["status"] = "OK"
print("REPORT_JSON: " + json.dumps(REPORT), flush=True)
