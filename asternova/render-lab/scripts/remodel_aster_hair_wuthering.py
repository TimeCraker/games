import bpy
import bmesh
import math
from mathutils import Vector

blend_path = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_head_base.blend"
out_render = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews\debug_wuthering_bangs.png"

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
# Delete old Hina front bangs (Islands 0, 1, 2, 3, 4)
for idx in [0, 1, 2, 3, 4]:
    if idx < len(islands):
        del_faces.extend(islands[idx])

# Delete old Hina side locks that flare out (Islands 5, 7, 8, 10, 11)
for idx in [5, 7, 8, 10, 11]:
    if idx < len(islands):
        del_faces.extend(islands[idx])

# Delete Ahoge (12, 13)
for idx in [12, 13]:
    if idx < len(islands):
        del_faces.extend(islands[idx])

# Delete chest braids (45-58)
for idx in range(45, len(islands)):
    del_faces.extend(islands[idx])

print(f"Deleting {len(del_faces)} old Hina faces...")
bmesh.ops.delete(bm, geom=del_faces, context='FACES')

# Delete isolated vertices
iso = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=iso, context='VERTS')

# 2. Function to create clean stylized anime hair clump
uv_lay = bm.loops.layers.uv.verify()

def add_wuthering_clump(bm, curve_pts, width_profile, u_tile=(0.02, 0.15), v_tile=(0.68, 0.81), mat_idx=0):
    n_pts = len(curve_pts)
    depth_profile = [w * 0.40 for w in width_profile]
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
        rad.z *= 0.35
        N = (rad - rad.dot(T) * T).normalized()
        B = T.cross(N).normalized()
        
        if i == n_pts - 1:
            v_tip = bm.verts.new(pos)
            cross_sections.append([v_tip, v_tip, v_tip])
        else:
            v_left  = bm.verts.new(pos - B * (w * 0.5) - N * (d * 0.25))
            v_mid   = bm.verts.new(pos + N * d)
            v_right = bm.verts.new(pos + B * (w * 0.5) - N * (d * 0.25))
            cross_sections.append([v_left, v_mid, v_right])
            
    # Connect faces & assign UVs
    u_min, u_max = u_tile
    u_mid_val = (u_min + u_max) * 0.5
    v_min, v_max = v_tile
    
    for i in range(n_pts - 1):
        vL0, vM0, vR0 = cross_sections[i]
        vL1, vM1, vR1 = cross_sections[i+1]
        
        t0 = i / float(n_pts - 1)
        t1 = (i + 1) / float(n_pts - 1)
        # V goes from root (v_max) to tip (v_min)
        v0 = v_max * (1.0 - t0) + v_min * t0
        v1 = v_max * (1.0 - t1) + v_min * t1
        
        if i == n_pts - 2:
            # Tip triangles
            f1 = bm.faces.new([vL0, vM0, vM1])
            f2 = bm.faces.new([vM0, vR0, vM1])
            f1.material_index = mat_idx
            f2.material_index = mat_idx
            f1.smooth = True
            f2.smooth = True
            
            for loop in f1.loops:
                if loop.vert == vL0: loop[uv_lay].uv = Vector((u_min, v0))
                elif loop.vert == vM0: loop[uv_lay].uv = Vector((u_mid_val, v0))
                elif loop.vert == vM1: loop[uv_lay].uv = Vector((u_mid_val, v1))
                
            for loop in f2.loops:
                if loop.vert == vM0: loop[uv_lay].uv = Vector((u_mid_val, v0))
                elif loop.vert == vR0: loop[uv_lay].uv = Vector((u_max, v0))
                elif loop.vert == vM1: loop[uv_lay].uv = Vector((u_mid_val, v1))
        else:
            # Quads
            f1 = bm.faces.new([vL0, vM0, vM1, vL1])
            f2 = bm.faces.new([vM0, vR0, vR1, vM1])
            f1.material_index = mat_idx
            f2.material_index = mat_idx
            f1.smooth = True
            f2.smooth = True
            
            for loop in f1.loops:
                if loop.vert == vL0: loop[uv_lay].uv = Vector((u_min, v0))
                elif loop.vert == vM0: loop[uv_lay].uv = Vector((u_mid_val, v0))
                elif loop.vert == vM1: loop[uv_lay].uv = Vector((u_mid_val, v1))
                elif loop.vert == vL1: loop[uv_lay].uv = Vector((u_min, v1))
                
            for loop in f2.loops:
                if loop.vert == vM0: loop[uv_lay].uv = Vector((u_mid_val, v0))
                elif loop.vert == vR0: loop[uv_lay].uv = Vector((u_max, v0))
                elif loop.vert == vR1: loop[uv_lay].uv = Vector((u_max, v1))
                elif loop.vert == vM1: loop[uv_lay].uv = Vector((u_mid_val, v1))

# 3. Add Aster's 2D-Turnaround Aligned Stylized Clumps
# Central Lock C1 (curves gently down to bridge of nose)
pts_c1 = [
    (0.000, 0.088, 1.625),
    (-0.004, 0.092, 1.585),
    (-0.008, 0.095, 1.545),
    (-0.012, 0.098, 1.510),
    (-0.014, 0.099, 1.485)
]
w_c1 = [0.013, 0.016, 0.015, 0.011, 0.002]
add_wuthering_clump(bm, pts_c1, w_c1)

# Left Inner Bang L1 (frames left inner eyebrow)
pts_l1 = [
    (-0.016, 0.086, 1.620),
    (-0.024, 0.090, 1.575),
    (-0.034, 0.093, 1.530),
    (-0.044, 0.094, 1.490),
    (-0.050, 0.093, 1.468)
]
w_l1 = [0.015, 0.018, 0.017, 0.012, 0.002]
add_wuthering_clump(bm, pts_l1, w_l1)

# Left Outer Bang L2 (frames outer left eye)
pts_l2 = [
    (-0.038, 0.084, 1.615),
    (-0.050, 0.088, 1.570),
    (-0.064, 0.090, 1.520),
    (-0.075, 0.087, 1.470),
    (-0.082, 0.082, 1.440)
]
w_l2 = [0.016, 0.020, 0.018, 0.013, 0.002]
add_wuthering_clump(bm, pts_l2, w_l2)

# Left Cheek-Framing Lock L3 (falls past ear along cheek)
pts_l3 = [
    (-0.068, 0.078, 1.600),
    (-0.082, 0.076, 1.540),
    (-0.092, 0.072, 1.470),
    (-0.096, 0.069, 1.400),
    (-0.092, 0.072, 1.350),
    (-0.080, 0.074, 1.320)
]
w_l3 = [0.016, 0.020, 0.020, 0.018, 0.014, 0.002]
add_wuthering_clump(bm, pts_l3, w_l3)

# Right Inner Bang R1 (frames right inner eyebrow)
pts_r1 = [
    (0.014, 0.086, 1.620),
    (0.022, 0.090, 1.575),
    (0.032, 0.092, 1.530),
    (0.040, 0.093, 1.490),
    (0.046, 0.092, 1.470)
]
w_r1 = [0.015, 0.018, 0.017, 0.012, 0.002]
add_wuthering_clump(bm, pts_r1, w_r1)

# Right Outer Bang R2 (frames outer right eye)
pts_r2 = [
    (0.035, 0.084, 1.615),
    (0.048, 0.087, 1.570),
    (0.060, 0.088, 1.520),
    (0.070, 0.085, 1.470),
    (0.076, 0.080, 1.445)
]
w_r2 = [0.016, 0.020, 0.018, 0.013, 0.002]
add_wuthering_clump(bm, pts_r2, w_r2)

# Right Cheek-Framing Lock R3 (falls past ear/flower along cheek)
pts_r3 = [
    (0.065, 0.078, 1.600),
    (0.080, 0.076, 1.540),
    (0.090, 0.072, 1.470),
    (0.094, 0.069, 1.400),
    (0.090, 0.072, 1.350),
    (0.078, 0.074, 1.320)
]
w_r3 = [0.016, 0.020, 0.020, 0.018, 0.014, 0.002]
add_wuthering_clump(bm, pts_r3, w_r3)

# Left Accent Layer (light layered strand)
pts_la = [
    (-0.026, 0.094, 1.590),
    (-0.038, 0.097, 1.550),
    (-0.048, 0.096, 1.515),
    (-0.054, 0.094, 1.490)
]
w_la = [0.012, 0.015, 0.012, 0.002]
add_wuthering_clump(bm, pts_la, w_la)

# Right Accent Layer (light layered strand)
pts_ra = [
    (0.024, 0.094, 1.590),
    (0.036, 0.097, 1.550),
    (0.045, 0.096, 1.515),
    (0.050, 0.094, 1.490)
]
w_ra = [0.012, 0.015, 0.012, 0.002]
add_wuthering_clump(bm, pts_ra, w_ra)

bm.to_mesh(hair.data)
bm.free()
hair.data.update()

# 4. Reload Aster natural flowing hair texture
tex_path = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\textures\aster_hair_texture.png"
hair_tex = bpy.data.images.load(tex_path, check_existing=False)
for mat in bpy.data.materials:
    if 'hair' in mat.name.lower() and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                node.image = hair_tex

# 5. Render Scene Setup
scene = bpy.data.scenes.new('WutheringRenderScene')
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
print("REMODEL WUTHERING BANGS COMPLETE!")
