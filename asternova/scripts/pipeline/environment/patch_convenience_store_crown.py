# -*- coding: utf-8 -*-
"""AsterNova - Assign a clean flat crown material to the convenience store's
parapet / awning-tip / soffit faces.

The Tripo atlas paints these thin crown surfaces with noisy mottled texels
(seen from outside as dead-noise patches). This script selects them by pure
geometry on the calibrated .blend (front = +Y, z up), assigns a dedicated
`mat_convenience_crown` flat material slot, and re-exports the .glb.

Gates (Blender space):
  crown  : center.z > 4.25                                  (roof / parapet top)
  awning : center.z > 3.55 and center.y > 6.1               (awning tip slab,
           excludes the fascia sign band at y <= 6.05)       extends past fascia)
  soffit : 2.55 < center.z < 3.6 and center.y > 5.2 and
           normal.y < -0.15                                  (awning underside)

Run: blender.exe -b --factory-startup -P patch_convenience_store_crown.py
In/Out: art/models/neighborhood/buildings/convenience_store/convenience_store.{blend,glb}
"""
import bpy
import os
from mathutils import Vector

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
BASE = os.path.join(REPO, r"art\models\neighborhood\buildings\convenience_store")
BLEND = os.path.join(BASE, "convenience_store.blend")
GLB = os.path.join(BASE, "convenience_store.glb")


def log(msg):
    print("[crown] " + str(msg), flush=True)


bpy.ops.wm.open_mainfile(filepath=BLEND)
body = [o for o in bpy.context.scene.objects if o.type == "MESH" and "Body" in o.name][0]

mat = bpy.data.materials.new("mat_convenience_crown")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.62, 0.60, 0.57, 1.0)
bsdf.inputs["Roughness"].default_value = 0.9

if "mat_convenience_crown" not in [m.name for m in body.data.materials]:
    body.data.materials.append(mat)
slot_idx = [m.name for m in body.data.materials].index("mat_convenience_crown")

mesh = body.data
selected = 0
for poly in mesh.polygons:
    c = poly.center
    n = poly.normal
    crown = c.z > 4.25
    awning = c.z > 3.55 and c.y > 6.1
    soffit = (2.55 < c.z < 3.6 and c.y > 5.2 and n.y < -0.15)
    sign_band = (c.y > 5.2 and abs(n.y) > 0.35 and abs(c.x) < 3.0)
    if (crown or awning or soffit) and not sign_band:
        poly.material_index = slot_idx
        selected += 1
log(f"faces assigned to crown material: {selected} / {len(mesh.polygons)}")

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
log(f"blend saved: {BLEND}")

bpy.ops.object.select_all(action="DESELECT")
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        o.select_set(True)
bpy.context.view_layer.objects.active = body
try:
    bpy.ops.export_scene.gltf(
        filepath=GLB, export_format="GLB", export_image_format="AUTO",
        export_yup=True,
    )
except TypeError:
    bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB")
log(f"glb exported: {GLB}")
