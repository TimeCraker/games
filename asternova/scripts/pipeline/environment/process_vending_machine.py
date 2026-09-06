# -*- coding: utf-8 -*-
"""AsterNova - Process dual vending machine prop (Phase 1 Ingestion).

Scale-calibrates the Tripo raw sculpt to the real-world Japanese street standard
height of 1.830m, grounds it to Z=0, centers it on the XY origin, applies all
transforms, then saves the .blend source and exports the game-ready .glb.

Also renders +Y/-Y probe previews (Workbench, textured) so the front-facing
convention can be verified visually; Aster's convention is front = +Y in
Blender == -Z in glTF/Godot (facing a Godot camera at +Z).

Run:
    blender.exe -b --factory-startup -P process_vending_machine.py
    blender.exe -b --factory-startup -P process_vending_machine.py -- --yaw 180

Inputs : art/models/neighborhood/props/vending_machine/vending_machine_dual_raw.glb
Outputs: art/models/neighborhood/props/vending_machine/vending_machine_dual.blend
         art/models/neighborhood/props/vending_machine/vending_machine_dual.glb
         %TEMP%/vm_probe_front_plusY.png / vm_probe_front_minusY.png
"""
import bpy
import os
import sys
import math
from mathutils import Matrix, Vector

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
RAW_GLB = os.path.join(
    REPO, r"art\models\neighborhood\props\vending_machine\vending_machine_dual_raw.glb"
)
OUT_DIR = os.path.join(REPO, r"art\models\neighborhood\props\vending_machine")
OUT_BLEND = os.path.join(OUT_DIR, "vending_machine_dual.blend")
OUT_GLB = os.path.join(OUT_DIR, "vending_machine_dual.glb")
PROBE_DIR = os.path.join(os.environ.get("TEMP", r"C:\Temp"), "vm_probe")

TARGET_HEIGHT = 1.830  # meters, Japanese street vending machine standard
FRONT_YAW_DEG = 0.0    # yaw applied so the front ends up facing Blender +Y

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--yaw" in argv:
    FRONT_YAW_DEG = float(argv[argv.index("--yaw") + 1])


def log(msg):
    print("[vending] " + str(msg), flush=True)


def world_bbox(objs):
    """Exact world-space bbox from evaluated mesh vertices."""
    deps = bpy.context.evaluated_depsgraph_get()
    xs, ys, zs = [], [], []
    for o in objs:
        ev = o.evaluated_get(deps)
        mw = ev.matrix_world
        for v in ev.data.vertices:
            w = mw @ v.co
            xs.append(w.x)
            ys.append(w.y)
            zs.append(w.z)
    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


def select_only(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


# ----------------------------------------------------------------------------
# 0. Clean scene and import raw glb
# ----------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=RAW_GLB)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    raise RuntimeError("no mesh objects found in raw glb")
roots = [o for o in bpy.context.scene.objects if o.parent is None]
log(f"imported: {len(meshes)} mesh(es), roots={[r.name for r in roots]}")

# ----------------------------------------------------------------------------
# 1. Uniform scale so total height == TARGET_HEIGHT
# ----------------------------------------------------------------------------
mn, mx = world_bbox(meshes)
orig_h = mx.z - mn.z
s = TARGET_HEIGHT / orig_h
log(f"raw size: w={mx.x-mn.x:.4f} d={mx.y-mn.y:.4f} h={orig_h:.4f}  scale={s:.6f}")

S = Matrix.Scale(s, 4)
for r in roots:
    r.matrix_world = S @ r.matrix_world
select_only(roots)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.view_layer.update()

# ----------------------------------------------------------------------------
# 2. Front orientation yaw (front must face Blender +Y before export)
# ----------------------------------------------------------------------------
if FRONT_YAW_DEG != 0.0:
    Rz = Matrix.Rotation(math.radians(FRONT_YAW_DEG), 4, "Z")
    for r in roots:
        r.matrix_world = Rz @ r.matrix_world
    select_only(roots)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.update()

# ----------------------------------------------------------------------------
# 3. Ground to Z=0 and center XY on origin, then apply
# ----------------------------------------------------------------------------
mn, mx = world_bbox(meshes)
delta = Vector((-(mn.x + mx.x) / 2.0, -(mn.y + mx.y) / 2.0, -mn.z))
for r in roots:
    r.matrix_world = Matrix.Translation(delta) @ r.matrix_world
select_only(roots)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.view_layer.update()

mn, mx = world_bbox(meshes)
height = mx.z - mn.z
log(f"calibrated: h={height:.5f} w={mx.x-mn.x:.5f} d={mx.y-mn.y:.5f} "
    f"zmin={mn.z:.6f} center_xy=({(mn.x+mx.x)/2:.6f},{(mn.y+mx.y)/2:.6f})")
assert abs(height - TARGET_HEIGHT) < 0.001, "height calibration failed"
assert abs(mn.z) < 0.001, "ground contact failed"

# ----------------------------------------------------------------------------
# 4. Probe renders (+Y and -Y views) to verify which side is the front
# ----------------------------------------------------------------------------
os.makedirs(PROBE_DIR, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.film_transparent = False
scene.world = scene.world or bpy.data.worlds.new("World")

cx, cy = (mn.x + mx.x) / 2.0, (mn.y + mx.y) / 2.0
cz = (mn.z + mx.z) / 2.0
dist = max(mx.x - mn.x, mx.y - mn.y) * 1.4 + 1.0

cam_data = bpy.data.cameras.new("ProbeCam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = max(mx.x - mn.x, mx.y - mn.y) * 1.25
cam = bpy.data.objects.new("ProbeCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

for tag, cam_y in (("minusY", cy - dist), ("plusY", cy + dist)):
    cam.location = (cx, cam_y, cz)
    direction = Vector((cx, cy, cz)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(PROBE_DIR, f"vm_probe_front_{tag}.png")
    bpy.ops.render.render(write_still=True)
    log(f"probe render saved: {scene.render.filepath}")

bpy.data.objects.remove(cam, do_unlink=True)
scene.camera = None

# ----------------------------------------------------------------------------
# 5. Save .blend source and export game .glb
# ----------------------------------------------------------------------------
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
log(f"blend saved: {OUT_BLEND}")

try:
    bpy.ops.export_scene.gltf(
        filepath=OUT_GLB,
        export_format="GLB",
        export_image_format="AUTO",
        export_yup=True,
    )
except TypeError:
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format="GLB")
log(f"glb exported: {OUT_GLB}")
log(f"[OK] calibrated to {TARGET_HEIGHT}m | yaw={FRONT_YAW_DEG}deg | "
    f"w={mx.x-mn.x:.4f} d={mx.y-mn.y:.4f} h={height:.4f}")
