# -*- coding: utf-8 -*-
"""AsterNova - Full processing for the corner convenience store landmark (Tier 2).

Pipeline (goal spec):
  1. Calibrate the raw Tripo FBX to 4.500m total height (incl. parapet + roof
     equipment), ground to Z=0, center XY, bake transforms.
  2. Yaw 180 deg so the storefront faces Blender +Y (== Godot -Z forward after
     glTF export, matching the vending machine / Aster convention).
  3. Decouple the storefront glass into its own material slot
     `mat_convenience_glass` (transparent, double-sided); walls keep
     `mat_convenience_store` with the 8K basecolor atlas.
  4. Open a >= 1.2m clear entrance: slide the entrance door panels sideways
     (parked, kept as glass) and delete the blocking storefront faces in the
     opening span so players can walk straight into the hollow interior.
  5. Save .blend source + export game .glb (embedded 8K albedo).

Run:
  blender.exe -b --factory-startup -P process_convenience_store_full.py -- --analyze
  blender.exe -b --factory-startup -P process_convenience_store_full.py -- --run
"""
import bpy
import bmesh
import os
import sys
import math
import collections
from mathutils import Matrix, Vector

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
BASE = os.path.join(REPO, r"art\models\neighborhood\buildings\convenience_store")
RAW_FBX = os.path.join(BASE, "convenience_store_raw.fbx")
TEX = os.path.join(BASE, r"textures\tex_convenience_store_basecolor.jpg")
OUT_BLEND = os.path.join(BASE, "convenience_store.blend")
OUT_GLB = os.path.join(BASE, "convenience_store.glb")

TARGET_HEIGHT = 4.500          # total incl. parapet + rooftop equipment
STOREFRONT_Z = (0.05, 2.90)    # storefront band world Z (incl. door transom)
FLUSH_EPS = 0.18               # front-plane flush tolerance (m)
MIN_OPENING = 1.20             # clear door width (m)
DOOR_SLIDE = 0.72              # sideways park distance per panel (m)
DOOR_DEPTH_SHIFT = 0.12        # park panels slightly inward to avoid z-fight
FRONT_NORMAL_Y = 0.50          # min forward normal component for storefront

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = "analyze"
if "--run" in argv:
    MODE = "run"

# --- empirical constants from the probe passes on this exact asset -------
# Raw Tripo mesh already faces +Y (verified: +Y side has the 24-sign
# storefront / -Y side the solid back kitchen). No yaw needed; +Y front
# exports to Godot -Z forward.
GLASS_Y_BAND = (5.20, 5.62)    # storefront glass plane Y range (front = +Y)
GLASS_X_MIN = -2.0             # tile wall sits left of this; keep opaque
GLASS_Z_BAND = (0.05, 2.90)    # glass height range incl. door transom
OPEN_X = (1.14, 2.80)          # entrance opening span (1.66m >= 1.2m clear)
DOOR_TOP_Z = 2.17              # below the opaque door header bar
OPEN_DEL_Y = (4.80, 6.10)      # blocker corridor depth range for deletion
DOOR_CX = 1.97                 # door center for L/R panel split


def log(msg):
    print("[csproc] " + str(msg), flush=True)


def world_bbox(objs):
    deps = bpy.context.evaluated_depsgraph_get()
    xs, ys, zs = [], [], []
    for o in objs:
        ev = o.evaluated_get(deps)
        mw = ev.matrix_world
        for v in ev.data.vertices:
            w = mw @ v.co
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


def select_only(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


# ----------------------------------------------------------------------------
# 0. import raw fbx
# ----------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=RAW_FBX)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
roots = [o for o in bpy.context.scene.objects if o.parent is None]
log(f"imported meshes={len(meshes)} roots={[r.name for r in roots]}")

# ----------------------------------------------------------------------------
# 1. calibrate: uniform scale to TARGET_HEIGHT, yaw 180 (front -> +Y),
#    ground to Z=0, center XY. Baked MANUALLY into mesh data — the
#    bpy.ops.object.transform_apply operator silently no-ops for rotations
#    in this headless setup, so operators are not used at all.
# ----------------------------------------------------------------------------
mn, mx = world_bbox(meshes)
s = TARGET_HEIGHT / (mx.z - mn.z)
log(f"raw {mx.x-mn.x:.4f} x {mx.y-mn.y:.4f} x {mx.z-mn.z:.4f}  scale={s:.6f}")

bpy.context.view_layer.update()
mn, mx = world_bbox(meshes)
# no yaw: the raw mesh already faces +Y; just scale and ground
M = (Matrix.Translation((0.0, 0.0, -mn.z)) @ Matrix.Scale(s, 4))
for o in meshes:
    o.data.transform(M)
    o.matrix_world = Matrix.Identity(4)
bpy.context.view_layer.update()

mn, mx = world_bbox(meshes)
delta = Vector((-(mn.x + mx.x) / 2.0, -(mn.y + mx.y) / 2.0, 0.0))
for o in meshes:
    o.data.transform(Matrix.Translation(delta))
    o.matrix_world = Matrix.Identity(4)
bpy.context.view_layer.update()

mn, mx = world_bbox(meshes)
log(f"calibrated: w={mx.x-mn.x:.4f} d={mx.y-mn.y:.4f} h={mx.z-mn.z:.4f} "
    f"zmin={mn.z:.6f} cx={(mn.x+mx.x)/2:.6f} cy={(mn.y+mx.y)/2:.6f}")
assert abs((mx.z - mn.z) - TARGET_HEIGHT) < 0.002
assert abs(mn.z) < 0.002

body = meshes[0]
# hard verification that transforms are baked into mesh DATA (not just the
# object matrix); the storefront side is mostly open glass, so it has LESS
# wall area than the solid back wall — front must be the +Y side
ys = [v.co.y for v in body.data.vertices]
assert abs(max(ys)) > 5.0, "scale not baked into mesh data"
pos_y = sum(p.area for p in body.data.polygons if p.normal.y > 0.5)
neg_y = sum(p.area for p in body.data.polygons if p.normal.y < -0.5)
log(f"mesh-space face area +Y={pos_y:.2f}m2 -Y={neg_y:.2f}m2 (storefront +Y)")
assert pos_y > neg_y, "orientation failed: glass storefront not facing +Y"

# ----------------------------------------------------------------------------
# 2. storefront analysis (front now = +Y)
# ----------------------------------------------------------------------------
y_front = mx.y
storefront = []  # (poly_index, center, normal, area)
for p in body.data.polygons:
    n = p.normal  # object space == world (transform baked)
    c = p.center
    if n.y > FRONT_NORMAL_Y and STOREFRONT_Z[0] < c.z < STOREFRONT_Z[1]:
        storefront.append((p.index, c, n, p.area))
log(f"storefront-band front faces: {len(storefront)}")

flush = [t for t in storefront if t[1].y > y_front - FLUSH_EPS]
recess = [t for t in storefront if t[1].y <= y_front - FLUSH_EPS]
log(f"flush={len(flush)} (area {sum(t[3] for t in flush):.2f}m2)  "
    f"recessed={len(recess)} (area {sum(t[3] for t in recess):.2f}m2)")
log(f"flush y range [{min((t[1].y for t in flush), default=0):.3f},{y_front:.3f}]  "
    f"recess y range [{min((t[1].y for t in recess), default=0):.3f},"
    f"{max((t[1].y for t in recess), default=0):.3f}]")

# fine Y histogram near the front to locate glass plane vs fascia vs props
near = [t for t in storefront if t[1].y > 4.5]
yh = collections.Counter(round(t[1].y * 20) / 20 for t in near)
log("front Y hist (0.05m): " + str(sorted(yh.items())))

# interior ceiling estimate: highest faces well inside the footprint
inner = [p for p in body.data.polygons
         if mn.x + 0.8 < p.center.x < mx.x - 0.8
         and mn.y + 0.8 < p.center.y < mx.y - 0.8
         and 0.05 < p.center.z < TARGET_HEIGHT - 0.4]
ceil_z = max((p.center.z for p in inner), default=0.0)
log(f"interior faces={len(inner)} estimated clear ceiling={ceil_z:.3f}m")

# ----------------------------------------------------------------------------
# 3. textured diagnostic renders (properly framed this time)
# ----------------------------------------------------------------------------
mat_wall = bpy.data.materials.new("mat_convenience_store")
mat_wall.use_nodes = True
bsdf = mat_wall.node_tree.nodes["Principled BSDF"]
tex_img = mat_wall.node_tree.nodes.new("ShaderNodeTexImage")
tex_img.image = bpy.data.images.load(TEX)
mat_wall.node_tree.links.new(tex_img.outputs["Color"], bsdf.inputs["Base Color"])
if body.data.materials:
    body.data.materials[0] = mat_wall
else:
    body.data.materials.append(mat_wall)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 864
scene.world = scene.world or bpy.data.worlds.new("World")

cam_data = bpy.data.cameras.new("DiagCam")
cam = bpy.data.objects.new("DiagCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
span = max(mx.x - mn.x, mx.y - mn.y)

# front 3/4 view (front = +Y, camera on the +Y side)
cam.location = (mx.x * 0.65, mx.y + span * 0.95, 2.6)
cam.rotation_euler = (Vector((0, mx.y, 2.2)) - Vector(cam.location)).to_track_quat("-Z", "Z").to_euler()
scene.render.filepath = os.path.join(BASE, "_diag_front34.png")
bpy.ops.render.render(write_still=True)
# straight-on front
cam.location = (0.0, mx.y + span * 1.05, 2.3)
cam.rotation_euler = (Vector((0, mx.y, 2.2)) - Vector(cam.location)).to_track_quat("-Z", "Z").to_euler()
scene.render.filepath = os.path.join(BASE, "_diag_front.png")
bpy.ops.render.render(write_still=True)
# interior view
cam.location = ((mn.x + mx.x) / 2 - 2.0, 0.5, 1.6)
cam.rotation_euler = (Vector((2.0, (mn.y + mx.y) / 2 + 2.0, 1.3)) - Vector(cam.location)).to_track_quat("-Z", "Z").to_euler()
scene.render.filepath = os.path.join(BASE, "_diag_interior.png")
bpy.ops.render.render(write_still=True)
# zoomed door-region render for visual door localization
cam_data2 = bpy.data.cameras.new("DoorCam")
cam2 = bpy.data.objects.new("DoorCam", cam_data2)
scene.collection.objects.link(cam2)
scene.camera = cam2
cam2.location = (DOOR_CX, mx.y + 5.0, 1.4)
cam2.rotation_euler = (Vector((DOOR_CX, mx.y, 1.2)) - Vector(cam2.location)).to_track_quat("-Z", "Z").to_euler()
cam_data2.lens = 35
scene.render.resolution_x = 900
scene.render.resolution_y = 1100
scene.render.filepath = os.path.join(BASE, "_diag_door_zoom.png")
bpy.ops.render.render(write_still=True)
scene.camera = cam
scene.render.resolution_x = 1280
scene.render.resolution_y = 864
bpy.data.objects.remove(cam2, do_unlink=True)
log("diagnostic renders written")

if MODE == "analyze":
    log("[ANALYZE DONE] - rerun with --run to produce assets")
    sys.exit(0)

# ----------------------------------------------------------------------------
# 4. entrance opening + glass decoupling  (MODE == run)
# ----------------------------------------------------------------------------
bm = bmesh.new()
bm.from_mesh(body.data)
bm.faces.ensure_lookup_table()

open_x0, open_x1 = OPEN_X
glass_keep_faces = []   # glass-plane faces outside opening -> glass mesh
door_panel_faces = []   # door slab faces -> duplicated as slid-open panels
del_faces = []          # every storefront blocker inside the opening span
for t in storefront:
    f = bm.faces[t[0]]
    if not f.is_valid:
        continue
    c, in_open = t[1], open_x0 <= t[1].x <= open_x1
    in_glass_plane = (GLASS_Y_BAND[0] <= c.y <= GLASS_Y_BAND[1]
                      and c.x >= GLASS_X_MIN)
    if in_open and c.z < DOOR_TOP_Z and OPEN_DEL_Y[0] <= c.y <= OPEN_DEL_Y[1]:
        del_faces.append(f)
        if in_glass_plane:
            door_panel_faces.append(f)
    elif in_glass_plane:
        glass_keep_faces.append(f)
log(f"glass keep={len(glass_keep_faces)} door panel={len(door_panel_faces)} "
    f"opening deletions={len(del_faces)}")
assert len(door_panel_faces) > 30, "door panels not found — thresholds wrong"
assert len(del_faces) > 40, "opening blockers not found — thresholds wrong"

# duplicate door panels (become the slid-open leaves), delete originals
panel_geo = bmesh.ops.duplicate(bm, geom=door_panel_faces)
panel_new_faces = [e for e in panel_geo["geom"] if isinstance(e, bmesh.types.BMFace)]
bmesh.ops.delete(bm, geom=del_faces, context="FACES")

pxs = [f.calc_center_median().x for f in panel_new_faces]
split_x = (min(pxs) + max(pxs)) / 2.0
hb = collections.Counter(round(x * 4) / 4 for x in pxs)
log(f"panel X range [{min(pxs):.3f},{max(pxs):.3f}] split at {split_x:.3f} "
    f"buckets={sorted(hb.items())}")
panels = {"L": [], "R": []}
for f in panel_new_faces:
    panels["L" if f.calc_center_median().x < split_x else "R"].append(f)

panel_objs = []
for side, faces in panels.items():
    if not faces:
        log(f"WARN: no {side} door panel faces")
        continue
    verts = set()
    for f in faces:
        verts.update(f.verts)
    pbm = bmesh.new()
    vmap = {v: pbm.verts.new(v.co) for v in verts}
    pbm.verts.ensure_lookup_table()
    for f in faces:
        try:
            pbm.faces.new([vmap[v] for v in f.verts])
        except ValueError:
            pass
    s = DOOR_SLIDE * (1 if side == "R" else -1)
    bmesh.ops.translate(pbm, verts=pbm.verts[:],
                        vec=Vector((s, -DOOR_DEPTH_SHIFT, 0)))
    me = bpy.data.meshes.new(f"ConvenienceStore_Door{side}")
    pbm.to_mesh(me)
    pbm.free()
    ob = bpy.data.objects.new(f"ConvenienceStore_Door{side}", me)
    scene.collection.objects.link(ob)
    panel_objs.append(ob)
    log(f"panel {side}: {len(faces)} faces, slid {s:+.2f}m")

# move kept glass faces out of body into their own mesh
verts = set()
for f in glass_keep_faces:
    if f.is_valid:
        verts.update(f.verts)
gbm = bmesh.new()
vmap = {v: gbm.verts.new(v.co) for v in verts}
gbm.verts.ensure_lookup_table()
kept = 0
for f in glass_keep_faces:
    if not f.is_valid:
        continue
    try:
        gbm.faces.new([vmap[v] for v in f.verts])
        kept += 1
    except ValueError:
        pass
log(f"glass faces kept: {kept}/{len(glass_keep_faces)}")

glass_mesh = bpy.data.meshes.new("ConvenienceStore_Glass")
gbm.to_mesh(glass_mesh)
gbm.free()
glass_obj = bpy.data.objects.new("ConvenienceStore_Glass", glass_mesh)
scene.collection.objects.link(glass_obj)

bmesh.ops.delete(bm, geom=[f for f in glass_keep_faces if f.is_valid],
                 context="FACES")
bm.to_mesh(body.data)
bm.free()
body.name = "ConvenienceStore_Body"

# ----------------------------------------------------------------------------
# 5. materials
# ----------------------------------------------------------------------------
mat_glass = bpy.data.materials.new("mat_convenience_glass")
mat_glass.use_nodes = True
g = mat_glass.node_tree.nodes["Principled BSDF"]
g.inputs["Base Color"].default_value = (0.85, 0.95, 1.0, 1.0)
g.inputs["Alpha"].default_value = 0.25
g.inputs["Roughness"].default_value = 0.05
g.inputs["Metallic"].default_value = 0.30
mat_glass.blend_method = "BLEND"
mat_glass.use_backface_culling = False

glass_obj.data.materials.append(mat_glass)
for ob in panel_objs:
    ob.data.materials.append(mat_glass)

# ----------------------------------------------------------------------------
# 6. save blend + export glb
# ----------------------------------------------------------------------------
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
log(f"blend saved: {OUT_BLEND}")

bpy.ops.object.select_all(action="DESELECT")
for o in (body, glass_obj, *panel_objs):
    o.select_set(True)
bpy.context.view_layer.objects.active = body
try:
    bpy.ops.export_scene.gltf(
        filepath=OUT_GLB, export_format="GLB", export_image_format="AUTO",
        export_yup=True, use_selection=True,
    )
except TypeError:
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format="GLB")
log(f"glb exported: {OUT_GLB}")

# final verification renders (front = +Y side)
cam.location = (mx.x * 0.65, mx.y + span * 0.95, 2.6)
cam.rotation_euler = (Vector((0, mx.y, 2.2)) - Vector(cam.location)).to_track_quat("-Z", "Z").to_euler()
scene.render.filepath = os.path.join(BASE, "_check_front34.png")
bpy.ops.render.render(write_still=True)
cam.location = (0.0, mx.y + span * 1.05, 2.3)
cam.rotation_euler = (Vector((0, mx.y, 2.2)) - Vector(cam.location)).to_track_quat("-Z", "Z").to_euler()
scene.render.filepath = os.path.join(BASE, "_check_front.png")
bpy.ops.render.render(write_still=True)
log("[RUN DONE]")
