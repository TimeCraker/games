import bpy
import bmesh
import math
from mathutils import Vector

blend_path = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_head_base.blend"
out_render = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews\debug_wuthering_v3.png"

bpy.ops.wm.open_mainfile(filepath=blend_path)

hair = bpy.data.objects.get('hair')
body = bpy.data.objects.get('body')
eyebrows = bpy.data.objects.get('eyebrows')
flower = bpy.data.objects.get('flower')

bm = bmesh.new()
bm.from_mesh(hair.data)
bm.faces.ensure_lookup_table()

# 1. Identify all islands in hair
visited = set()
islands = []
for f in bm.faces:
    if f in visited: continue
    isl = []
    q = [f]
    visited.add(f)
    while q:
        c = q.pop(0)
        isl.append(c)
        for e in c.edges:
            for n in e.link_faces:
                if n not in visited:
                    visited.add(n)
                    q.append(n)
    islands.append(isl)

del_faces = []
# For Islands 0 and 2: KEEP the crown root (where any vertex z > 1.57), delete only the lower hanging slabs (z <= 1.57)
for idx in [0, 2]:
    if idx < len(islands):
        for f in islands[idx]:
            # If all verts are below 1.575, delete
            if max(v.co.z for v in f.verts) < 1.575:
                del_faces.append(f)

# Delete Island 1 (center overlapping block) entirely
if 1 < len(islands): del_faces.extend(islands[1])
# Delete Island 3 and 4 (small messy front pieces)
for idx in [3, 4]:
    if idx < len(islands): del_faces.extend(islands[idx])

# Delete Ahoge (12, 13)
for idx in [12, 13]:
    if idx < len(islands): del_faces.extend(islands[idx])

# Delete chest braids (45-58)
for idx in range(45, len(islands)):
    del_faces.extend(islands[idx])

# Delete flaring side curls (5, 7, 8, 10, 11)
for idx in [5, 7, 8, 10, 11]:
    if idx < len(islands): del_faces.extend(islands[idx])

print(f"Deleting {len(del_faces)} faces...")
bmesh.ops.delete(bm, geom=del_faces, context='FACES')

# Delete isolated vertices
iso = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=iso, context='VERTS')

# 2. Function to create CLOSED, watertight stylized anime hair clump
uv_lay = bm.loops.layers.uv.verify()

def add_closed_wuthering_clump(bm, curve_pts, width_profile, u_tile=(0.36, 0.61), v_tile=(0.08, 0.32), mat_idx=0):
    n_pts = len(curve_pts)
    depth_profile = [w * 0.38 for w in width_profile]
    head_center = Vector((0.0, 0.015, 1.50))
    cross_sections = []
    
    for i in range(n_pts):
        pos = Vector(curve_pts[i])
        w = width_profile[i]
        d = depth_profile[i]
        
        if i == 0:
            T = (Vector(curve_pts[1]) - pos).normalized()
        elif i == n_pts - 1:
            T = (pos - Vector(curve_pts[i-1])).normalized()
        else:
            T = (Vector(curve_pts[i+1]) - Vector(curve_pts[i-1])).normalized()
            
        rad = (pos - head_center)
        rad.z *= 0.30
        N = (rad - rad.dot(T) * T).normalized()
        B = T.cross(N).normalized()
        
        if i == n_pts - 1:
            v_tip = bm.verts.new(pos)
            cross_sections.append([v_tip, v_tip, v_tip])
        else:
            v_left  = bm.verts.new(pos - B * (w * 0.5) - N * (d * 0.30))
            v_mid   = bm.verts.new(pos + N * d)
            v_right = bm.verts.new(pos + B * (w * 0.5) - N * (d * 0.30))
            cross_sections.append([v_left, v_mid, v_right])
            
    u_min, u_max = u_tile
    u_mid_val = (u_min + u_max) * 0.5
    v_min, v_max = v_tile
    
    # Root cap: triangle [vL0, vR0, vM0]
    vL0, vM0, vR0 = cross_sections[0]
    f_root = bm.faces.new([vL0, vR0, vM0])
    f_root.material_index = mat_idx
    f_root.smooth = True
    for loop in f_root.loops:
        loop[uv_lay].uv = Vector((u_mid_val, v_max))
        
    for i in range(n_pts - 1):
        vL_a, vM_a, vR_a = cross_sections[i]
        vL_b, vM_b, vR_b = cross_sections[i+1]
        
        t0 = i / float(n_pts - 1)
        t1 = (i + 1) / float(n_pts - 1)
        v0 = v_max * (1.0 - t0) + v_min * t0
        v1 = v_max * (1.0 - t1) + v_min * t1
        
        if i == n_pts - 2:
            f_fl = bm.faces.new([vL_a, vM_a, vM_b])
            f_fr = bm.faces.new([vM_a, vR_a, vM_b])
            f_bk = bm.faces.new([vR_a, vL_a, vM_b])
            for f in [f_fl, f_fr, f_bk]:
                f.material_index = mat_idx
                f.smooth = True
            for loop in f_fl.loops:
                if loop.vert == vL_a: loop[uv_lay].uv = Vector((u_min, v0))
                elif loop.vert == vM_a: loop[uv_lay].uv = Vector((u_mid_val, v0))
                elif loop.vert == vM_b: loop[uv_lay].uv = Vector((u_mid_val, v1))
            for loop in f_fr.loops:
                if loop.vert == vM_a: loop[uv_lay].uv = Vector((u_mid_val, v0))
                elif loop.vert == vR_a: loop[uv_lay].uv = Vector((u_max, v0))
                elif loop.vert == vM_b: loop[uv_lay].uv = Vector((u_mid_val, v1))
            for loop in f_bk.loops:
                if loop.vert == vR_a: loop[uv_lay].uv = Vector((u_max, v0))
                elif loop.vert == vL_a: loop[uv_lay].uv = Vector((u_min, v0))
                elif loop.vert == vM_b: loop[uv_lay].uv = Vector((u_mid_val, v1))
        else:
            f_fl = bm.faces.new([vL_a, vM_a, vM_b, vL_b])
            f_fr = bm.faces.new([vM_a, vR_a, vR_b, vM_b])
            f_bk = bm.faces.new([vR_a, vL_a, vL_b, vR_b])
            for f in [f_fl, f_fr, f_bk]:
                f.material_index = mat_idx
                f.smooth = True
            for loop in f_fl.loops:
                if loop.vert == vL_a: loop[uv_lay].uv = Vector((u_min, v0))
                elif loop.vert == vM_a: loop[uv_lay].uv = Vector((u_mid_val, v0))
                elif loop.vert == vM_b: loop[uv_lay].uv = Vector((u_mid_val, v1))
                elif loop.vert == vL_b: loop[uv_lay].uv = Vector((u_min, v1))
            for loop in f_fr.loops:
                if loop.vert == vM_a: loop[uv_lay].uv = Vector((u_mid_val, v0))
                elif loop.vert == vR_a: loop[uv_lay].uv = Vector((u_max, v0))
                elif loop.vert == vR_b: loop[uv_lay].uv = Vector((u_max, v1))
                elif loop.vert == vM_b: loop[uv_lay].uv = Vector((u_mid_val, v1))
            for loop in f_bk.loops:
                if loop.vert == vR_a: loop[uv_lay].uv = Vector((u_max, v0))
                elif loop.vert == vL_a: loop[uv_lay].uv = Vector((u_min, v0))
                elif loop.vert == vL_b: loop[uv_lay].uv = Vector((u_min, v1))
                elif loop.vert == vR_b: loop[uv_lay].uv = Vector((u_max, v1))

# 3. Add Aster's Stylized Clumps emerging under crown line
# Central Lock C1 (curves gently down to bridge of nose, leaves forehead window on both sides)
pts_c1 = [
    (-0.002, 0.080, 1.600),
    (-0.004, 0.086, 1.565),
    (-0.007, 0.091, 1.530),
    (-0.010, 0.094, 1.498),
    (-0.012, 0.095, 1.478)
]
w_c1 = [0.014, 0.018, 0.016, 0.011, 0.002]
add_closed_wuthering_clump(bm, pts_c1, w_c1)

# Left Inner Bang L1 (frames left inner brow, curves outward)
pts_l1 = [
    (-0.016, 0.078, 1.595),
    (-0.025, 0.084, 1.555),
    (-0.036, 0.088, 1.515),
    (-0.046, 0.090, 1.478),
    (-0.052, 0.089, 1.455)
]
w_l1 = [0.016, 0.020, 0.018, 0.012, 0.002]
add_closed_wuthering_clump(bm, pts_l1, w_l1)

# Left Outer Bang L2 (frames outer left eye)
pts_l2 = [
    (-0.038, 0.076, 1.590),
    (-0.052, 0.082, 1.550),
    (-0.066, 0.085, 1.505),
    (-0.076, 0.082, 1.460),
    (-0.082, 0.077, 1.428)
]
w_l2 = [0.016, 0.022, 0.019, 0.013, 0.002]
add_closed_wuthering_clump(bm, pts_l2, w_l2)

# Left Face-Framing Lock L3 (falls smoothly along cheek past ear)
pts_l3 = [
    (-0.070, 0.070, 1.590),
    (-0.084, 0.068, 1.530),
    (-0.093, 0.064, 1.460),
    (-0.095, 0.061, 1.390),
    (-0.090, 0.064, 1.340),
    (-0.078, 0.066, 1.310)
]
w_l3 = [0.016, 0.021, 0.021, 0.018, 0.014, 0.002]
add_closed_wuthering_clump(bm, pts_l3, w_l3)

# Right Inner Bang R1 (frames right inner brow, curves outward)
pts_r1 = [
    (0.014, 0.078, 1.595),
    (0.023, 0.084, 1.555),
    (0.034, 0.088, 1.515),
    (0.043, 0.090, 1.478),
    (0.049, 0.089, 1.455)
]
w_r1 = [0.016, 0.020, 0.018, 0.012, 0.002]
add_closed_wuthering_clump(bm, pts_r1, w_r1)

# Right Outer Bang R2 (frames outer right eye)
pts_r2 = [
    (0.035, 0.076, 1.590),
    (0.049, 0.082, 1.550),
    (0.062, 0.085, 1.505),
    (0.072, 0.082, 1.460),
    (0.078, 0.077, 1.428)
]
w_r2 = [0.016, 0.022, 0.019, 0.013, 0.002]
add_closed_wuthering_clump(bm, pts_r2, w_r2)

# Right Face-Framing Lock R3 (falls smoothly along cheek past ear)
pts_r3 = [
    (0.068, 0.070, 1.590),
    (0.082, 0.068, 1.530),
    (0.091, 0.064, 1.460),
    (0.093, 0.061, 1.390),
    (0.088, 0.064, 1.340),
    (0.076, 0.066, 1.310)
]
w_r3 = [0.016, 0.021, 0.021, 0.018, 0.014, 0.002]
add_closed_wuthering_clump(bm, pts_r3, w_r3)

# Left Accent Layer (light layered strand)
pts_la = [
    (-0.022, 0.088, 1.585),
    (-0.033, 0.092, 1.545),
    (-0.044, 0.092, 1.505),
    (-0.050, 0.090, 1.478)
]
w_la = [0.012, 0.015, 0.012, 0.002]
add_closed_wuthering_clump(bm, pts_la, w_la)

# Right Accent Layer (light layered strand)
pts_ra = [
    (0.020, 0.088, 1.585),
    (0.031, 0.092, 1.545),
    (0.041, 0.092, 1.505),
    (0.046, 0.090, 1.478)
]
w_ra = [0.012, 0.015, 0.012, 0.002]
add_closed_wuthering_clump(bm, pts_ra, w_ra)

bm.to_mesh(hair.data)
bm.free()
hair.data.update()

# 4. Reload updated hair texture
tex_path = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\textures\aster_hair_texture.png"
hair_tex = bpy.data.images.load(tex_path, check_existing=False)
for mat in bpy.data.materials:
    if 'hair' in mat.name.lower() and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                node.image = hair_tex

# 5. Render Scene Setup
scene = bpy.data.scenes.new('WutheringRenderSceneV3')
bpy.context.window.scene = scene

world = bpy.data.worlds.new('WhiteStudio')
world.use_nodes = True
nodes_w = world.node_tree.nodes
nodes_w.clear()
bg = nodes_w.new('ShaderNodeBackground')
bg.inputs['Color'].default_value = (0.95, 0.95, 0.96, 1.0)
out_w = nodes_w.new('ShaderNodeOutputWorld')
world.node_tree.links.new(bg.outputs['Background'], out_w.inputs['Surface'])
scene.world = world

col = bpy.data.collections.new('Col')
scene.collection.children.link(col)
for o in [body, hair, eyebrows, flower, bpy.data.objects.get('eye.l'), bpy.data.objects.get('eye.r')]:
    if o: col.objects.link(o)

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024

l1 = bpy.data.lights.new('Key', 'SUN')
l1.energy = 1.6
o1 = bpy.data.objects.new('Key', l1)
col.objects.link(o1)
o1.rotation_euler = (math.radians(-5), math.radians(10), math.radians(180))

l2 = bpy.data.lights.new('Fill', 'SUN')
l2.energy = 1.1
l2.color = (0.92, 0.95, 1.0)
o2 = bpy.data.objects.new('Fill', l2)
col.objects.link(o2)
o2.rotation_euler = (math.radians(5), math.radians(-10), math.radians(180))

cam_d = bpy.data.cameras.new('FrontCam')
cam_d.lens = 85
cam_o = bpy.data.objects.new('FrontCam', cam_d)
col.objects.link(cam_o)
scene.camera = cam_o
cam_o.location = (0, 0.88, 1.445)
cam_o.rotation_euler = (math.radians(90), 0, math.radians(180))

scene.render.filepath = out_render
bpy.ops.render.render(write_still=True)
print("REMODEL WUTHERING V3 COMPLETE!")
