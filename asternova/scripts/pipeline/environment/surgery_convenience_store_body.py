# -*- coding: utf-8 -*-
"""AsterNova - Convenience store body surgery (Phase 1/2 finisher).

Operates on the ALREADY endfield-rebuilt convenience_store.blend (gondolas /
counter / LED / sign text exist as separate objects) and fixes the remaining
hard defects found in the 5th-iteration review renders:

  1. delete the broken horizontal "glass" planes (ConvenienceStore_Glass[R])
     and every old glass/degenerate face inside the facade window band
     (they formed the diagonal shard and the floating sliver);
  2. rebuild the storefront glass as true vertical orthogonal quad grids with
     aluminum mullion frames, leaving the 1.66m door opening untouched;
  3. re-assign every face inside the store volume to a clean warm-white
     mat_pbr_interior (kills the blurry 2D supermarket photo walls);
  4. repaint the whole facade sign-band zone with mat_pbr_aluminum
     (kills the AI junk glyphs "020 0..." / "K&CE&S...");
  5. purge leftover loose geometry / tiny disconnected islands;
  6. bevel the lightbox panel + band 1.2cm.

Run: blender.exe -b --factory-startup -P surgery_convenience_store_body.py
In/Out: convenience_store.{blend,glb}  (+ %TEMP% verification renders)
"""
import bpy
import bmesh
import os
import sys
from mathutils import Matrix, Vector

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
BASE = os.path.join(REPO, r"art\models\neighborhood\buildings\convenience_store")
BLEND = os.path.join(BASE, "convenience_store.blend")
GLB = os.path.join(BASE, "convenience_store.glb")
TMP = os.environ.get("TEMP", r"C:\Temp")

# facade window band (blend space: front = +Y, z up)
BAND_Y = (5.70, 6.06)      # facade wall thickness zone
BAND_Z = (0.50, 2.55)      # window band vertical span
DOOR_X = (0.36, 2.40)      # keep the door opening faces untouched
GLASS_Y = 5.87             # new glass plane (just inside the facade)
INTERIOR_BOX = (6.30, 5.78, 3.45)  # |x|, |y|, z  -> interior paint volume


def log(m):
    print("[surgery] " + str(m), flush=True)


bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene

# ---------------------------------------------------------------- materials
def flat_mat(name, color, rough=0.85, metal=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


MAT_INTERIOR = flat_mat("mat_pbr_interior", (0.87, 0.86, 0.82), rough=0.90)
MAT_ALU = bpy.data.materials.get("mat_pbr_aluminum") or flat_mat(
    "mat_pbr_aluminum", (0.16, 0.17, 0.19), rough=0.40, metal=0.85)
MAT_GLASS = bpy.data.materials.get("mat_convenience_glass")
assert MAT_GLASS is not None, "mat_convenience_glass missing"

# ---------------------------------------------------------------- 0. idempotent pre-clean
STALE = [o.name for o in scene.objects if o.type == "MESH"
         and o.name.startswith(("StorefrontGlass", "StorefrontMullion", "StorefrontTransom"))]
for o in list(scene.objects):
    if o.type == "MESH" and o.name.startswith(("StorefrontGlass", "StorefrontMullion", "StorefrontTransom")):
        bpy.data.objects.remove(o, do_unlink=True)
log(f"pre-clean removed: {STALE}")

# ---------------------------------------------------------------- 1. broken glass objects
gone = [o.name for o in scene.objects if o.type == "MESH"
        and o.name.startswith("ConvenienceStore_Glass")]
for o in list(scene.objects):
    if o.type == "MESH" and o.name.startswith("ConvenienceStore_Glass"):
        bpy.data.objects.remove(o, do_unlink=True)
log(f"removed broken glass objects: {gone}")

# ---------------------------------------------------------------- 2. body surgery
body = [o for o in scene.objects if o.type == "MESH" and o.name == "ConvenienceStore_Body"][0]
log(f"body world matrix identity: {body.matrix_world == Matrix.Identity(4)}")

bm = bmesh.new()
bm.from_mesh(body.data)
bm.faces.ensure_lookup_table()


def in_band(c):
    return BAND_Y[0] <= c.y <= BAND_Y[1] and BAND_Z[0] <= c.z <= BAND_Z[1]


def in_door(c):
    return DOOR_X[0] <= c.x <= DOOR_X[1]


def is_old_glass(c, n):
    """Old glass shard zone: reaches deep into the store behind the window band."""
    if abs(n.y) <= 0.35:
        return False
    if not (0.35 <= c.z <= 2.60):
        return False
    if not (4.90 <= c.y <= 6.06):
        return False
    if DOOR_X[0] <= c.x <= DOOR_X[1]:
        return c.y <= 5.74  # vestibule faces behind the doors only
    return True


def is_exterior_zone(c):
    return c.y > 5.5 or c.y < -5.5 or abs(c.x) > 6.0


# 2a. delete old glass / degenerate faces inside the window band (skip door)
del_faces = []
for f in bm.faces:
    c = f.calc_center_median()
    n = f.normal
    if (in_band(c) or is_old_glass(c, n)) and not in_door(c) and abs(n.y) > 0.5:
        del_faces.append(f)
    elif is_old_glass(c, n):
        del_faces.append(f)
log(f"window-band faces to delete: {len(del_faces)}")
bmesh.ops.delete(bm, geom=del_faces, context="FACES")
bm.faces.ensure_lookup_table()

# 2b. re-assign: sign band -> aluminum, interior volume -> warm interior paint
alum, inter = 0, 0
slots = {s.material.name if s.material else "": i
         for i, s in enumerate(body.material_slots)}
if "mat_pbr_aluminum" not in slots:
    body.data.materials.append(MAT_ALU)
    slots = {s.material.name if s.material else "": i
             for i, s in enumerate(body.material_slots)}
if "mat_pbr_interior" not in slots:
    body.data.materials.append(MAT_INTERIOR)
    slots = {s.material.name if s.material else "": i
             for i, s in enumerate(body.material_slots)}
i_alu = slots["mat_pbr_aluminum"]
i_int = slots["mat_pbr_interior"]
for f in bm.faces:
    c = f.calc_center_median()
    n = f.normal
    if BAND_Z[1] < c.z < 4.65 and is_exterior_zone(c):
        f.material_index = i_alu
        alum += 1
        continue
    # 内表面通用判定：中心在建筑足印内，且沿法线前移 12cm 的探点仍在店内体积
    if (0.0 < c.z < 3.5 and abs(c.x) < 6.35 and abs(c.y) < 6.03
            and abs(c.x + n.x * 0.12) < 6.32 and abs(c.y + n.y * 0.12) < 5.95
            and 0.05 < c.z + n.z * 0.12 < 3.40):
        f.material_index = i_int
        inter += 1
log(f"reassigned: aluminum band={alum}, interior={inter}")

# 2c. loose verts + tiny islands purge
bmesh.ops.delete(bm, geom=[v for v in bm.verts if len(v.link_faces) == 0],
                 context="VERTS")
bm.faces.ensure_lookup_table()
seen = set()
comps = []
for f in bm.faces:
    if f.index in seen:
        continue
    comp, stack = [], [f]
    seen.add(f.index)
    while stack:
        cur = stack.pop()
        comp.append(cur)
        for e in cur.edges:
            for lf in e.link_faces:
                if lf.index not in seen:
                    seen.add(lf.index)
                    stack.append(lf)
    comps.append(comp)
comps.sort(key=len, reverse=True)
purged = 0
for comp in comps[1:]:
    if len(comp) <= 64:  # small floating islands only; big shells stay
        bmesh.ops.delete(bm, geom=comp, context="FACES")
        purged += len(comp)
log(f"components={len(comps)} purged_small_islands_faces={purged}")
bm.to_mesh(body.data)
bm.free()
body.data.update()
log(f"body polys now={len(body.data.polygons)}")

# ---------------------------------------------------------------- 2d. panel-opening sliver purge
# 灯箱开口内的墙体残留薄片（重涂铝色后呈暗色 tick/发丝线，凸出面板前方）
bm2 = bmesh.new()
bm2.from_mesh(body.data)
bm2.faces.ensure_lookup_table()
slivers = []
for f in bm2.faces:
    c = f.calc_center_median()
    if c.y > 5.99 and abs(c.x) < 6.38 and 2.56 < c.z < 4.54:
        slivers.append(f)
if slivers:
    bmesh.ops.delete(bm2, geom=slivers, context="FACES")
    bmesh.ops.delete(bm2, geom=[v for v in bm2.verts if len(v.link_faces) == 0],
                     context="VERTS")
bm2.to_mesh(body.data)
bm2.free()
body.data.update()
log(f"panel-opening slivers deleted: {len(slivers)}")

# ---------------------------------------------------------------- 3. new storefront glass
def glass_pane(name, x0, x1, z0, z1, nx):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=nx, y_subdivisions=2,
                                    size=1, calc_uvs=True)
    o = bpy.context.active_object
    o.name = name
    o.scale = (x1 - x0, z1 - z0, 1)
    o.rotation_euler = (1.5707963, 0, 0)  # grid XY -> XZ vertical, normal +/-Y
    bpy.ops.object.transform_apply(rotation=True, scale=True)
    o.location = ((x0 + x1) / 2, GLASS_Y, (z0 + z1) / 2)
    bpy.ops.object.transform_apply(location=True)
    o.data.materials.clear()
    o.data.materials.append(MAT_GLASS)
    return o


def mullion(name, x0, x1, z0, z1):
    return box(name, x1 - x0, 0.07, z1 - z0,
               ((x0 + x1) / 2, GLASS_Y + 0.02, (z0 + z1) / 2), MAT_ALU)


def box(name, sx, sy, sz, pos, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    if mat:
        o.data.materials.append(mat)
    return o


PANES = [(-6.35, 0.36, "L"), (2.40, 6.35, "R")]
for x0, x1, side in PANES:
    z0, z1 = BAND_Z
    g = glass_pane(f"StorefrontGlass_{side}", x0, x1, z0, z1,
                   max(2, int((x1 - x0) / 1.05)))
    log(f"glass pane {side}: x[{x0},{x1}] faces={len(g.data.polygons)}")
    mullion(f"StorefrontMullion_{side}_L", x0 - 0.03, x0 + 0.03, z0, z1)
    mullion(f"StorefrontMullion_{side}_R", x1 - 0.03, x1 + 0.03, z0, z1)
    mullion(f"StorefrontMullion_{side}_T", x0, x1, z1 - 0.03, z1 + 0.03)
    mullion(f"StorefrontMullion_{side}_B", x0, x1, z0 - 0.03, z0 + 0.03)
    mid = (x0 + x1) / 2
    mullion(f"StorefrontMullion_{side}_M", mid - 0.025, mid + 0.025, z0, z1)
    mullion(f"StorefrontTransom_{side}", x0, x1, 1.83 - 0.025, 1.83 + 0.025)

# ---------------------------------------------------------------- 4. bevel lightbox 1.2cm
for name in ("SignPanel", "SignBand"):
    o = scene.objects.get(name)
    if not o:
        continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                    offset=0.012, segments=2, profile=0.7, affect="EDGES",
                    clamp_overlap=True)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    log(f"beveled {name}")

# ---------------------------------------------------------------- 4b. sign text off-panel junk
SIGN_X_KEEP = {"SignText_Main": 3.00, "SignText_Sub": 1.40}
for name, xkeep in SIGN_X_KEEP.items():
    o = scene.objects.get(name)
    if not o:
        continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    mw = o.matrix_world
    def face_bad(f):
        for v in f.verts:
            w = mw @ v.co
            if not (2.40 <= w.z <= 4.70) or abs(w.x) > xkeep:
                return True
        return False
    junk = [f for f in bm.faces if face_bad(f)]
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if len(v.link_faces) == 0],
                         context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    log(f"sign text {name}: removed {len(junk)} off-panel faces")

# ---------------------------------------------------------------- 5. save + export + probes
bpy.ops.wm.save_mainfile()
log(f"blend saved")

bpy.ops.object.select_all(action="DESELECT")
for o in scene.objects:
    if o.type == "MESH":
        o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB",
                          export_image_format="AUTO", use_selection=True,
                          export_yup=True)
log(f"glb exported: {GLB}")

# verification renders (workbench textured, ortho-ish)
cam_data = bpy.data.cameras.new("VerifyCam")
cam = bpy.data.objects.new("VerifyCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.render.resolution_x = 900
scene.render.resolution_y = 620
os.makedirs(os.path.join(TMP, "cs_surgery"), exist_ok=True)
for tag, pos, tgt in (("front", (2.0, 13.5, 2.1), (0.3, 2.0, 1.7)),
                      ("interior", (1.4, 1.8, 1.55), (-2.5, -0.5, 0.9))):
    cam.location = pos
    d = Vector(tgt) - Vector(pos)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = 28
    scene.render.filepath = os.path.join(TMP, "cs_surgery", f"verify_{tag}.png")
    bpy.ops.render.render(write_still=True)
    log(f"verify render {tag} saved")
log("[OK] surgery complete")
