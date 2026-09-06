# -*- coding: utf-8 -*-
"""AsterNova - Endfield industrial rework of the corner convenience store.

Phase 1  geometry surgery on the calibrated .blend (front = +Y, z up):
  - delete non-shell furniture components (old photo-back shelving / counters)
  - delete stray loose geometry and tiny floating islands (悬空飞刃)
  - rebuild the storefront glass as a clean orthogonal quad grid
  - bevel hard edges 1.2cm (parapet / awning / door frame)
Phase 2  facade PBR zoning:
  - shell exterior -> light cold-gray architectural concrete
  - sign band faces removed and replaced by a clean lightbox + vector text
    ("24H SUPPLY STATION / CONVENIENCE", dark extruded type)
Phase 3  interior 3D fittings (replaces every 2D photo panel):
  - double-sided gondola shelving units with instanced low-poly product boxes
  - L-shaped register counter with screen + scanner by the entrance right
  - 3 recessed LED strip panels on the ceiling line

Run: blender.exe -b --factory-startup -P rebuild_convenience_store_endfield.py
In/Out: convenience_store.{blend,glb}  (+ %TEMP% verification renders)
"""
import bpy
import bmesh
import os
import random
from mathutils import Vector, Matrix

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
BASE = os.path.join(REPO, r"art\models\neighborhood\buildings\convenience_store")
BLEND = os.path.join(BASE, "convenience_store.blend")
GLB = os.path.join(BASE, "convenience_store.glb")
TMP = os.environ.get("TEMP", r"C:\Temp")

random.seed(20260906)


def log(msg):
    print("[rebuild] " + str(msg), flush=True)


# ---------------------------------------------------------------- materials
def flat_mat(name, color, rough=0.85, metal=0.0, emit=None, emit_str=0.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
    # 材质已存在时也刷新参数（.blend 里存的是上一轮数值）
    b = None
    for node in m.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            b = node
            break
    if b is None:
        b = m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1.0)
        b.inputs["Emission Strength"].default_value = emit_str
    return m


def box(name, sx, sy, sz, pos, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    if mat:
        o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------- open
bpy.ops.wm.open_mainfile(filepath=BLEND)
body = [o for o in bpy.context.scene.objects if o.type == "MESH" and "Body" in o.name][0]

# idempotent pre-clean: drop anything a previous run generated
STALE_PREFIX = ("SignPanel", "SignText", "SignBand", "Gondola", "Counter",
                "Register", "Scanner", "LEDStrip", "Products_", "Fittings_",
                "EntryMat", "PromoTable", "PromoTop", "Promo_prod", "ConvenienceStore_Glass")
stale = [o for o in bpy.context.scene.objects
         if o.type == "MESH" and o.name.startswith(STALE_PREFIX)]
for o in stale:
    bpy.data.objects.remove(o, do_unlink=True)
log(f"pre-clean removed {len(stale)} stale objects")

MAT_CONCRETE = flat_mat("mat_pbr_concrete", (0.66, 0.68, 0.70), rough=0.80)
MAT_ALU = flat_mat("mat_pbr_aluminum", (0.16, 0.17, 0.19), rough=0.40, metal=0.85)
MAT_LIGHTBOX = flat_mat("mat_pbr_lightbox", (0.45, 0.45, 0.44), rough=0.5,
                        emit=(0.95, 0.93, 0.88), emit_str=1.0)
MAT_SIGN_TEXT = flat_mat("mat_pbr_sign_text", (0.05, 0.06, 0.07), rough=0.6)
MAT_GONDOLA = flat_mat("mat_pbr_gondola", (0.55, 0.57, 0.60), rough=0.55)
MAT_SHELF = flat_mat("mat_pbr_shelf", (0.78, 0.76, 0.72), rough=0.6)
MAT_COUNTER = flat_mat("mat_pbr_counter", (0.85, 0.84, 0.81), rough=0.45)
MAT_COUNTER_BODY = flat_mat("mat_pbr_counter_body", (0.42, 0.45, 0.48), rough=0.6)
MAT_LED = flat_mat("mat_pbr_led", (0.30, 0.30, 0.32), rough=0.4,
                   emit=(1.0, 0.88, 0.70), emit_str=0.9)
MAT_SCREEN = flat_mat("mat_pbr_screen", (0.08, 0.10, 0.12), rough=0.2,
                      emit=(0.35, 0.55, 0.85), emit_str=1.6)
PROD_COLORS = [
    flat_mat("mat_prod_a", (0.72, 0.20, 0.16), rough=0.5),
    flat_mat("mat_prod_b", (0.16, 0.42, 0.24), rough=0.5),
    flat_mat("mat_prod_c", (0.16, 0.30, 0.58), rough=0.5),
    flat_mat("mat_prod_d", (0.82, 0.62, 0.18), rough=0.5),
]
log(f"body polys={len(body.data.polygons)}")

# ---------------------------------------------------------------- Phase 1a
# delete old furniture: connected components other than the building shell
bm = bmesh.new()
bm.from_mesh(body.data)
bm.faces.ensure_lookup_table()
sets = []
seen = set()
for f in bm.faces:
    if f.index in seen:
        continue
    comp = []
    stack = [f]
    seen.add(f.index)
    while stack:
        cur = stack.pop()
        comp.append(cur)
        for e in cur.edges:
            for lf in e.link_faces:
                if lf.index not in seen:
                    seen.add(lf.index)
                    stack.append(lf)
    sets.append(comp)
sets.sort(key=len, reverse=True)
shell = sets[0]
log(f"components={len(sets)} shell_faces={len(shell)}")
furn_faces = set()
for comp in sets[1:]:
    for f in comp:
        furn_faces.add(f.index)
log(f"furniture faces to delete: {len(furn_faces)}")
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in sorted(furn_faces)],
                 context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if len(v.link_faces) == 0],
                 context="VERTS")
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.002)
bm.to_mesh(body.data)
bm.free()
body.data.update()

# 店内地板：素色混凝土材质槽（PBR rough 0.92 无镜面 hot-spot，消阳光穿门死白）
floor_mat = flat_mat("mat_pbr_floor", (0.42, 0.41, 0.40), rough=0.92)
if "mat_pbr_floor" not in [m.name for m in body.data.materials]:
    body.data.materials.append(floor_mat)
floor_idx = [m.name for m in body.data.materials].index("mat_pbr_floor")
n_floor = 0
for poly in body.data.polygons:
    c = poly.center
    n = poly.normal
    if (n.z > 0.7 and c.z < 0.30 and abs(c.x) < 6.4 and -5.6 < c.y < 5.6):
        poly.material_index = floor_idx
        n_floor += 1
log(f"interior floor faces -> mat_pbr_floor: {n_floor}")

# 左墙外侧旧 24 招牌（-X 朝外面板）：并入冠部素色材质，消店内透视镜像旧牌
crown_idx = None
for mi_, m_ in enumerate(body.data.materials):
    if m_ and m_.name == "mat_convenience_crown":
        crown_idx = mi_
if crown_idx is not None:
    n_sign = 0
    for poly in body.data.polygons:
        c = poly.center
        n = poly.normal
        if n.x < -0.7 and 2.3 < c.z < 4.8 and c.x < -5.6:
            poly.material_index = crown_idx
            n_sign += 1
    log(f"left exterior sign faces -> crown: {n_sign}")
log(f"after furniture purge + loose cleanup: polys={len(body.data.polygons)}")

# ---------------------------------------------------------------- Phase 1b
# rebuild storefront glass as clean orthogonal quad grid (normal = +Y outward)
glass_mat = bpy.data.materials.get("mat_convenience_glass")
grid = bpy.ops.mesh.primitive_grid_add(x_subdivisions=9, y_subdivisions=3,
                                       size=1, calc_uvs=True)
gobj = bpy.context.active_object
gobj.name = "ConvenienceStore_Glass"
# storefront spans x -6.35..1.10 (left of door) and 2.85..3.35 (right pane)
# built in two halves via one grid then split: simpler -> scale a full grid to
# the left pane and add a small right pane object
gobj.scale = ((1.10 - (-6.35)), 1.0, (2.68 - 0.55))
gobj.location = ((-6.35 + 1.10) / 2, 5.45, (0.55 + 2.68) / 2)
bpy.ops.object.transform_apply(scale=True, location=True)
gobj.data.materials.append(glass_mat)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.normals_make_consistent()
bpy.ops.object.mode_set(mode="OBJECT")
log(f"left glass grid: {len(gobj.data.polygons)} faces")

pane2 = bpy.ops.mesh.primitive_grid_add(x_subdivisions=1, y_subdivisions=3,
                                        size=1, calc_uvs=True)
p2 = bpy.context.active_object
p2.name = "ConvenienceStore_GlassR"
p2.scale = (3.35 - 2.85, 1.0, 2.68 - 0.55)
p2.location = ((2.85 + 3.35) / 2, 5.45, (0.55 + 2.68) / 2)
bpy.ops.object.transform_apply(scale=True, location=True)
p2.data.materials.append(glass_mat)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.normals_make_consistent()
bpy.ops.object.mode_set(mode="OBJECT")

# ---------------------------------------------------------------- Phase 2
# sign band: remove old fascia faces on the front crown band, build lightbox
bm = bmesh.new()
bm.from_mesh(body.data)
bm.faces.ensure_lookup_table()
kill = []
for f in bm.faces:
    c = f.calc_center_median()
    if c.y > 5.3 and 2.5 < c.z < 4.6:
        kill.append(f)
log(f"fascia faces removed for lightbox: {len(kill)}")
bmesh.ops.delete(bm, geom=kill, context="FACES")
bm.to_mesh(body.data)
bm.free()

# lightbox: white panel box across the front crown (full width), dark text
sign_panel = box("SignPanel", 12.9, 0.10, 1.94, (0.0, 5.98, 3.63), MAT_LIGHTBOX)
# dark text: two extruded text objects
def add_text(name, body_str, size, pos, mat, extrude=0.02, align_x="CENTER"):
    bpy.ops.object.text_add(location=pos)
    t = bpy.context.active_object
    t.name = name
    t.data.body = body_str
    t.data.size = size
    t.data.extrude = extrude
    t.data.align_x = align_x
    t.data.align_y = "CENTER"
    t.rotation_euler = (math.pi / 2, 0, math.pi)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


import math
t1 = add_text("SignText_Main", "24H SUPPLY STATION", 0.60,
              (0.0, 6.06, 3.95), MAT_SIGN_TEXT)
t2 = add_text("SignText_Sub", "CONVENIENCE", 0.38,
              (0.0, 6.06, 3.25), MAT_SIGN_TEXT)
# thin colored band strip under the text (Endfield accent, matte dark)
band = box("SignBand", 12.9, 0.02, 0.12, (0.0, 6.03, 2.72), MAT_ALU)

# ---------------------------------------------------------------- Phase 3
# interior fittings: gondolas + products + L counter + LED strips
GONDOLA_POS = [(-5.35, 0.0, 0.0), (5.35, 0.0, 0.0),
               (-1.5, -1.2, math.pi / 2), (-1.5, 1.4, math.pi / 2)]
prod_meshes = []
prod_objs = []


def make_prod(name, mat, sx, sy, sz, pos):
    o = box(name, sx, sy, sz, pos, mat)
    prod_objs.append(o)
    return o


def gondola(name, cx, cy, rot_z):
    parent_cols = []
    cosv, sinv = math.cos(rot_z), math.sin(rot_z)

    def P(lx, ly, lz):
        return (cx + lx * cosv - ly * sinv, cy + lx * sinv + ly * cosv, lz)

    box(f"{name}_base", 2.4, 0.6, 0.16, P(0, 0, 0.08), MAT_GONDOLA)
    box(f"{name}_back", 2.4, 0.05, 1.75, P(0, 0, 0.95), MAT_GONDOLA)
    for side in (-1, 1):
        for zz in (0.5, 0.95, 1.4, 1.85):
            box(f"{name}_shelf", 2.3, 0.42, 0.03, P(0, side * 0.28, zz), MAT_SHELF)
            # product boxes front row on each shelf
            n = random.randint(6, 9)
            x0 = -1.05
            for k in range(n):
                px = x0 + k * (2.1 / (n - 1))
                h = random.uniform(0.16, 0.30)
                make_prod(f"{name}_prod", PROD_COLORS[random.randrange(4)],
                          random.uniform(0.12, 0.20), 0.16, h,
                          P(px, side * 0.24, zz + 0.015 + h / 2))


for idx, (gx, gy, gr) in enumerate(GONDOLA_POS):
    gondola(f"Gondola{idx}", gx, gy, gr)

# L-shaped register counter (entrance right, Blender x 2.6..5.2 / y 4.35..5.45)
box("Counter_Main", 2.6, 0.7, 0.92, (3.9, 4.7, 0.46), MAT_COUNTER_BODY)
box("Counter_Top", 2.75, 0.8, 0.05, (3.9, 4.7, 0.945), MAT_COUNTER)
box("Counter_Return", 0.7, 0.9, 0.92, (5.15, 4.9, 0.46), MAT_COUNTER_BODY)
box("Counter_ReturnTop", 0.8, 1.0, 0.05, (5.15, 4.9, 0.945), MAT_COUNTER)
box("Register_Screen", 0.42, 0.06, 0.34, (3.15, 4.78, 1.28), MAT_SCREEN)
box("Register_Stand", 0.06, 0.06, 0.30, (3.15, 4.78, 1.05), MAT_ALU)
box("Scanner", 0.24, 0.20, 0.08, (3.7, 4.72, 1.005), MAT_SCREEN)

# promo stack-out table over the sun-patch inside the door (diegetic)
box("PromoTable", 1.0, 0.62, 0.46, (0.8, 1.8, 0.23), MAT_COUNTER_BODY)
box("PromoTop", 1.1, 0.7, 0.04, (0.8, 1.8, 0.48), MAT_COUNTER)
for k in range(6):
    make_prod("Promo_prod", PROD_COLORS[k % 4], 0.16, 0.12, 0.20,
              (0.45 + k * 0.14, 1.8, 0.60))

# entry doormat inside the door (kills sun spec hotspot, diegetic)
MAT_MAT = flat_mat("mat_pbr_doormat", (0.24, 0.25, 0.27), rough=0.95)
box("EntryMat", 2.3, 1.1, 0.02, (1.97, 4.9, 0.012), MAT_MAT)

# 3 ceiling LED strip panels along the central aisle
for i, (lx, ly) in enumerate(((0.6, 2.6), (0.2, 0.3), (-0.2, -2.2))):
    box(f"LEDStrip{i}", 2.2, 0.32, 0.05, (lx, ly, 3.36), MAT_LED)

# join fittings into one object per material is overkill; group under a parent
fittings_objs = [o for o in bpy.context.scene.objects
                 if o.type == "MESH" and o.name.startswith(("Gondola", "Counter",
                                                            "Register", "Scanner",
                                                            "LEDStrip", "Sign",
                                                            "ConvenienceStore_Glass"))]
log(f"fittings meshes: {len(fittings_objs)} total tris≈"
    f"{sum(len(o.data.polygons) for o in fittings_objs)}")

# ---------------------------------------------------------------- joins
# merge fittings into few meshes (single-draw-call groups)
def join_group(prefix, new_name, contains=None):
    grp = [o for o in bpy.context.scene.objects if o.type == "MESH"
           and (o.name.startswith(prefix) or (contains and contains in o.name))]
    if not grp:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in grp:
        o.select_set(True)
    bpy.context.view_layer.objects.active = grp[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = new_name
    log(f"joined {len(grp)} -> {new_name} ({len(joined.data.polygons)} faces)")
    return joined


join_group("Gondola", "Fittings_Gondolas")
for ci, cm in enumerate(PROD_COLORS):
    grp = [o for o in bpy.context.scene.objects if o.type == "MESH"
           and o.data.materials and o.data.materials[0] == cm]
    if not grp:
        continue
    bpy.ops.object.select_all(action="DESELECT")
    for o in grp:
        o.select_set(True)
    bpy.context.view_layer.objects.active = grp[0]
    bpy.ops.object.join()
    bpy.context.active_object.name = f"Products_{ci}"
    log(f"joined products color {ci}: {len(grp)} objs")
join_group("Counter", "Fittings_Counter")
join_group("Register", "Fittings_Register", contains="Scanner")
join_group("LEDStrip", "Fittings_LED")

# ---------------------------------------------------------------- Phase 1c
# bevel hard edges 1.2cm on the building shell (angle-limited)
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
bpy.context.view_layer.objects.active = body
mod = body.modifiers.new("Bevel", "BEVEL")
mod.width = 0.012
mod.segments = 1
mod.limit_method = "ANGLE"
mod.angle_limit = math.radians(45)
mod.use_clamp_overlap = True
bpy.context.view_layer.objects.active = body
bpy.ops.object.modifier_apply(modifier="Bevel")
log(f"after bevel: polys={len(body.data.polygons)}")

# ---------------------------------------------------------------- save/export
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
log(f"blend saved: {BLEND}")
bpy.ops.object.select_all(action="DESELECT")
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        o.select_set(True)
bpy.context.view_layer.objects.active = body
try:
    bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB",
                              export_image_format="AUTO", export_yup=True)
except TypeError:
    bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB")
log(f"glb exported: {GLB} ({os.path.getsize(GLB) // 1024} KiB)")

# ---------------------------------------------------------------- verification
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.render.resolution_x = 1024
scene.render.resolution_y = 640
cam_d = bpy.data.cameras.new("VerifyCam")
cam_d.lens = 30
cam = bpy.data.objects.new("VerifyCam", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam
for tag, pos, tgt in (("ext", (0.4, -11.0, 1.5), (0.8, 4.0, 1.4)),
                      ("int", (-0.8, 3.6, 1.62), (1.8, -1.5, 1.0)),
                      ("top", (0.0, 0.0, 14.0), (0.0, 0.0, 0.0))):
    cam.location = pos
    d = Vector(tgt) - Vector(pos)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(TMP, f"cs_rebuild_{tag}.png")
    bpy.ops.render.render(write_still=True)
    log(f"verify render: {scene.render.filepath}")
log("[OK] rebuild complete")
