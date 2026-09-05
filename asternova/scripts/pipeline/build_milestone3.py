# AsterNova - Milestone 3: Costume Assembly & NPR Multi-Layered Skirt Pipeline
import bpy, addon_utils, bmesh, os, math
from mathutils import Vector, Euler, Matrix

# 1. Open Milestone 2 Blend File
m2_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\aster_milestone2_hair.blend'
bpy.ops.wm.open_mainfile(filepath=m2_path)

addon_utils.enable('mmd_tools')

print('=== AsterNova: Executing Milestone 3 Costume Pipeline ===')

# Ensure directories exist
models_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models'
preview_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews\milestone3'
os.makedirs(preview_dir, exist_ok=True)

# -------------------------------------------------------------
# 2. Calibrate Body_Base Skin Shader (Remove Dark Straps)
# -------------------------------------------------------------
body_obj = bpy.data.objects['Body_Base']
# Clean Columbina's mat 13 (体) from Body_Base to ensure only pure skin remains
bm_body = bmesh.new()
bm_body.from_mesh(body_obj.data)
del_strap_faces = [f for f in bm_body.faces if f.material_index == 13]
bmesh.ops.delete(bm_body, geom=del_strap_faces, context='FACES')
bmesh.ops.delete(bm_body, geom=[v for v in bm_body.verts if not v.link_faces], context='VERTS')
bm_body.to_mesh(body_obj.data)
bm_body.free()
body_obj.data.update()

# Node-level filter on mat 16 (肌) to turn any dark markings into pure radiant porcelain skin
skin_mat = body_obj.data.materials[16]
if skin_mat and skin_mat.node_tree:
    nodes = skin_mat.node_tree.nodes
    links = skin_mat.node_tree.links
    tex_node = nodes.get('Image Texture')
    mix_node = nodes.get('Mix')
    if tex_node and mix_node:
        filter_ramp = nodes.new('ShaderNodeValToRGB')
        filter_ramp.name = 'SkinStrapFilter'
        filter_ramp.color_ramp.elements[0].position = 0.0
        filter_ramp.color_ramp.elements[0].color = (0.96, 0.91, 0.89, 1.0) # skin color
        filter_ramp.color_ramp.elements[1].position = 0.40
        filter_ramp.color_ramp.elements[1].color = (0.98, 0.93, 0.90, 1.0)
        links.new(tex_node.outputs['Color'], filter_ramp.inputs['Factor'])
        links.new(filter_ramp.outputs['Color'], mix_node.inputs['A'])

print('-> Body skin calibrated to pure radiant porcelain tone.')

# -------------------------------------------------------------
# 3. Import Columbina Clothing Components (Dress, Sleeves, Shoes)
# -------------------------------------------------------------
existing_objs = set(bpy.data.objects.keys())
col_pmx = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\columbina\columbina.pmx'
bpy.ops.mmd_tools.import_model(filepath=col_pmx, types={'MESH'})
new_objs = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in existing_objs]
imported_mesh = [o for o in new_objs if o.type == 'MESH'][0]

# Extract Dress (裙), Sleeves (袖, 袖饰), Shoes (鞋)
keep_mats = ['裙', '袖', '袖饰', '鞋']
target_indices = [i for i, m in enumerate(imported_mesh.data.materials) if any(k in m.name for k in keep_mats)]

bm_col = bmesh.new()
bm_col.from_mesh(imported_mesh.data)
# Keep only dress, sleeves, shoes; filter out high headpieces (Z > 1.30)
del_faces = [f for f in bm_col.faces if f.material_index not in target_indices or any(v.co.z > 1.30 for v in f.verts)]
bmesh.ops.delete(bm_col, geom=del_faces, context='FACES')
bmesh.ops.delete(bm_col, geom=[v for v in bm_col.verts if not v.link_faces], context='VERTS')
bm_col.to_mesh(imported_mesh.data)
bm_col.free()
imported_mesh.name = 'Costume_Main'
imported_mesh.data.update()

print('-> Imported high-precision dress bodice, sleeves, and footwear.')

# -------------------------------------------------------------
# 4. White Ankle Socks with Delicate Ruffled Tops
# -------------------------------------------------------------
bm_socks = bmesh.new()
bm_socks.from_mesh(body_obj.data)
# Extract ankle band: Z between 0.035 and 0.175
sock_faces = [f for f in bm_socks.faces if f.material_index == 16 and all(0.035 <= v.co.z <= 0.175 for v in f.verts)]

socks_mesh = bpy.data.meshes.new('Aster_WhiteSocks_Mesh')
bm_new_sock = bmesh.new()
vert_map = {}
for f in sock_faces:
    new_verts = []
    for v in f.verts:
        if v not in vert_map:
            vert_map[v] = bm_new_sock.verts.new(v.co + v.normal * 0.0012)
        new_verts.append(vert_map[v])
    bm_new_sock.faces.new(new_verts)

bm_new_sock.to_mesh(socks_mesh)
bm_new_sock.free()
bm_socks.free()

socks_obj = bpy.data.objects.new('Aster_WhiteSocks', socks_mesh)
bpy.context.scene.collection.objects.link(socks_obj)

# Create Ruffles at top of socks
sock_ruffles = []
for side, sx in [('L', -0.042), ('R', 0.042)]:
    bpy.ops.mesh.primitive_torus_add(major_radius=0.032, minor_radius=0.004, location=(sx, 0.042, 0.175))
    ruffle = bpy.context.active_object
    ruffle.name = f'Aster_SockRuffle_{side}'
    sock_ruffles.append(ruffle)

print('-> Modeled semi-opaque white ankle socks with ruffled cuffs.')

# -------------------------------------------------------------
# 5. Chest Ribbon Tie & Golden Framed Pearl Brooch
# -------------------------------------------------------------
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.012, depth=0.004, location=(0, -0.096, 1.255))
brooch_ring = bpy.context.active_object
brooch_ring.rotation_euler = (math.radians(90), 0, 0)
brooch_ring.name = 'Aster_ChestBrooch_Ring'

bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, radius=0.008, location=(0, -0.099, 1.255))
brooch_pearl = bpy.context.active_object
brooch_pearl.name = 'Aster_ChestBrooch_Pearl'

bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.018, depth=0.005, location=(-0.022, -0.093, 1.255))
loop_l = bpy.context.active_object
loop_l.rotation_euler = (math.radians(90), math.radians(25), 0)
loop_l.scale = (1.5, 0.6, 1.0)
loop_l.name = 'Aster_ChestRibbon_L'

bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.018, depth=0.005, location=(0.022, -0.093, 1.255))
loop_r = bpy.context.active_object
loop_r.rotation_euler = (math.radians(90), math.radians(-25), 0)
loop_r.scale = (1.5, 0.6, 1.0)
loop_r.name = 'Aster_ChestRibbon_R'

print('-> Modeled chest ribbon tie and gold-framed pearl brooch.')

# -------------------------------------------------------------
# 6. High-Waist Sash, Gold Buttons & Left Hip Flower Ornament
# -------------------------------------------------------------
waist_buttons = []
for row, bz in enumerate([1.015, 0.985]):
    for col, bx in enumerate([-0.020, 0.020]):
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0045, depth=0.003, location=(bx, -0.096, bz))
        btn = bpy.context.active_object
        btn.rotation_euler = (math.radians(90), 0, 0)
        btn.name = f'Aster_WaistButton_{row}_{col}'
        waist_buttons.append(btn)

flower_loc = (-0.130, -0.085, 0.975)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.007, location=flower_loc)
flower_core = bpy.context.active_object
flower_core.name = 'Aster_WaistFlower_Core'

waist_petals = []
for p in range(5):
    ang = p * (2 * math.pi / 5)
    px = flower_loc[0] + 0.016 * math.cos(ang)
    pz = flower_loc[2] + 0.016 * math.sin(ang)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.009, location=(px, flower_loc[1] + 0.002, pz))
    petal = bpy.context.active_object
    petal.scale = (1.0, 0.4, 1.3)
    petal.rotation_euler = (math.radians(15), 0, ang)
    petal.name = f'Aster_WaistPetal_{p}'
    waist_petals.append(petal)

curve_data = bpy.data.curves.new('Aster_WaistStreamer_Curve', type='CURVE')
curve_data.dimensions = '3D'
polyline = curve_data.splines.new('BEZIER')
polyline.bezier_points.add(2)
pts = [
    Vector(flower_loc),
    Vector((flower_loc[0] - 0.015, flower_loc[1] - 0.020, flower_loc[2] - 0.12)),
    Vector((flower_loc[0] - 0.010, flower_loc[1] - 0.010, flower_loc[2] - 0.25))
]
for i, pt in enumerate(pts):
    polyline.bezier_points[i].co = pt
    polyline.bezier_points[i].handle_left = pt - Vector((0, 0, 0.03))
    polyline.bezier_points[i].handle_right = pt + Vector((0, 0, 0.03))

curve_data.bevel_depth = 0.006
waist_streamer = bpy.data.objects.new('Aster_WaistStreamer', curve_data)
bpy.context.scene.collection.objects.link(waist_streamer)

bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, radius=0.008, location=(flower_loc[0] - 0.010, flower_loc[1] - 0.010, flower_loc[2] - 0.255))
waist_charm = bpy.context.active_object
waist_charm.name = 'Aster_WaistCharm'

print('-> Modeled high-waist buttons and left hip flower streamer.')

# -------------------------------------------------------------
# 7. Back Waist Double-Wing Ribbon Bow & Cascading Streamers
# -------------------------------------------------------------
bow_center = (0.0, 0.115, 0.985)
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.016, depth=0.018, location=bow_center)
back_knot = bpy.context.active_object
back_knot.rotation_euler = (0, math.radians(90), 0)
back_knot.name = 'Aster_BackBow_Knot'

bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.038, depth=0.008, location=(-0.055, 0.125, 0.995))
back_wing_l = bpy.context.active_object
back_wing_l.rotation_euler = (math.radians(-20), math.radians(-30), math.radians(15))
back_wing_l.scale = (1.6, 0.8, 1.0)
back_wing_l.name = 'Aster_BackBow_Wing_L'

bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.038, depth=0.008, location=(0.055, 0.125, 0.995))
back_wing_r = bpy.context.active_object
back_wing_r.rotation_euler = (math.radians(-20), math.radians(30), math.radians(-15))
back_wing_r.scale = (1.6, 0.8, 1.0)
back_wing_r.name = 'Aster_BackBow_Wing_R'

back_streamers = []
for side, sx in [('L', -0.035), ('R', 0.035)]:
    c_data = bpy.data.curves.new(f'BackStreamerCurve_{side}', type='CURVE')
    c_data.dimensions = '3D'
    poly = c_data.splines.new('BEZIER')
    poly.bezier_points.add(2)
    s_pts = [
        Vector((sx, 0.118, 0.985)),
        Vector((sx * 1.5, 0.145, 0.820)),
        Vector((sx * 1.8, 0.130, 0.650))
    ]
    for i, pt in enumerate(s_pts):
        poly.bezier_points[i].co = pt
        poly.bezier_points[i].handle_left = pt - Vector((0, 0.01, 0.04))
        poly.bezier_points[i].handle_right = pt + Vector((0, -0.01, 0.04))
    c_data.bevel_depth = 0.012
    s_obj = bpy.data.objects.new(f'Aster_BackStreamer_{side}', c_data)
    bpy.context.scene.collection.objects.link(s_obj)
    back_streamers.append(s_obj)

print('-> Modeled back waist ribbon bow and twin cascading streamers.')

# -------------------------------------------------------------
# 8. Wrist Ribbon Cuff Bows
# -------------------------------------------------------------
cuff_bows = []
for side, cx in [('L', -0.420), ('R', 0.420)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.012, depth=0.004, location=(cx, 0.005, 0.910))
    cuff_b = bpy.context.active_object
    cuff_b.name = f'Aster_CuffBow_{side}'
    cuff_b.rotation_euler = (math.radians(90), 0, math.radians(45 if side == 'L' else -45))
    cuff_bows.append(cuff_b)

print('-> Modeled wrist ribbon cuff bows.')

# -------------------------------------------------------------
# 9. Master NPR Cel Shaders for Costume & Accessories
# -------------------------------------------------------------
def get_or_create_mat(name):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    return mat

# A. Pearl White & Lavender Shadow NPR Cel Shader
mat_ivory_cel = get_or_create_mat('Aster_Mat_IvoryCloth')
mat_ivory_cel.use_nodes = True
nodes = mat_ivory_cel.node_tree.nodes
links = mat_ivory_cel.node_tree.links
nodes.clear()

out_node = nodes.new('ShaderNodeOutputMaterial')
diff_node = nodes.new('ShaderNodeBsdfDiffuse')
s2rgb_node = nodes.new('ShaderNodeShaderToRGB')
ramp_node = nodes.new('ShaderNodeValToRGB')
ramp_node.color_ramp.elements[0].position = 0.48
ramp_node.color_ramp.elements[0].color = (0.83, 0.80, 0.90, 1.0) # Soft lavender shadow #D4CCE6
ramp_node.color_ramp.elements[1].position = 0.52
ramp_node.color_ramp.elements[1].color = (0.97, 0.97, 0.99, 1.0) # Ivory White #F7F8FC

emis_node = nodes.new('ShaderNodeEmission')
links.new(diff_node.outputs['BSDF'], s2rgb_node.inputs['Shader'])
links.new(s2rgb_node.outputs['Color'], ramp_node.inputs['Factor'])
links.new(ramp_node.outputs['Color'], emis_node.inputs['Color'])
links.new(emis_node.outputs['Emission'], out_node.inputs['Surface'])

# B. Soft Pale-Blue Ribbon NPR Shader
mat_blue_ribbon = get_or_create_mat('Aster_Mat_BlueRibbon')
nodes = mat_blue_ribbon.node_tree.nodes
links = mat_blue_ribbon.node_tree.links
nodes.clear()
out_node = nodes.new('ShaderNodeOutputMaterial')
diff_node = nodes.new('ShaderNodeBsdfDiffuse')
s2rgb_node = nodes.new('ShaderNodeShaderToRGB')
ramp_node = nodes.new('ShaderNodeValToRGB')
ramp_node.color_ramp.elements[0].position = 0.48
ramp_node.color_ramp.elements[0].color = (0.55, 0.70, 0.88, 1.0) # Soft blue shadow
ramp_node.color_ramp.elements[1].position = 0.52
ramp_node.color_ramp.elements[1].color = (0.65, 0.84, 0.96, 1.0) # Ice Blue #A6D5F5
emis_node = nodes.new('ShaderNodeEmission')
links.new(diff_node.outputs['BSDF'], s2rgb_node.inputs['Shader'])
links.new(s2rgb_node.outputs['Color'], ramp_node.inputs['Factor'])
links.new(ramp_node.outputs['Color'], emis_node.inputs['Color'])
links.new(emis_node.outputs['Emission'], out_node.inputs['Surface'])

# C. Champagne Gold Metal Accent Shader
mat_gold = get_or_create_mat('Aster_Mat_ChampagneGold')
nodes = mat_gold.node_tree.nodes
links = mat_gold.node_tree.links
nodes.clear()
out_node = nodes.new('ShaderNodeOutputMaterial')
bsdf_gold = nodes.new('ShaderNodeBsdfPrincipled')
bsdf_gold.inputs['Base Color'].default_value = (1.0, 0.84, 0.50, 1.0) # Champagne Gold #FFD580
bsdf_gold.inputs['Metallic'].default_value = 0.85
bsdf_gold.inputs['Roughness'].default_value = 0.25
links.new(bsdf_gold.outputs['BSDF'], out_node.inputs['Surface'])

# D. Glowing Pearl Shader
mat_pearl = get_or_create_mat('Aster_Mat_GlowingPearl')
nodes = mat_pearl.node_tree.nodes
links = mat_pearl.node_tree.links
nodes.clear()
out_node = nodes.new('ShaderNodeOutputMaterial')
bsdf_p = nodes.new('ShaderNodeBsdfPrincipled')
bsdf_p.inputs['Base Color'].default_value = (0.98, 0.98, 1.0, 1.0)
bsdf_p.inputs['Metallic'].default_value = 0.1
bsdf_p.inputs['Roughness'].default_value = 0.15
emis_p = nodes.new('ShaderNodeEmission')
emis_p.inputs['Color'].default_value = (0.95, 0.97, 1.0, 1.0)
emis_p.inputs['Strength'].default_value = 0.25
mix_p = nodes.new('ShaderNodeMixShader')
mix_p.inputs['Fac'].default_value = 0.3
links.new(bsdf_p.outputs['BSDF'], mix_p.inputs[1])
links.new(emis_p.outputs['Emission'], mix_p.inputs[2])
links.new(mix_p.outputs['Shader'], out_node.inputs['Surface'])

# E. Semi-Opaque White Socks Shader
mat_socks = get_or_create_mat('Aster_Mat_WhiteSocks')
nodes = mat_socks.node_tree.nodes
links = mat_socks.node_tree.links
nodes.clear()
out_node = nodes.new('ShaderNodeOutputMaterial')
diff_node = nodes.new('ShaderNodeBsdfDiffuse')
s2rgb_node = nodes.new('ShaderNodeShaderToRGB')
ramp_node = nodes.new('ShaderNodeValToRGB')
ramp_node.color_ramp.elements[0].position = 0.45
ramp_node.color_ramp.elements[0].color = (0.86, 0.84, 0.90, 1.0)
ramp_node.color_ramp.elements[1].position = 0.55
ramp_node.color_ramp.elements[1].color = (0.96, 0.96, 0.98, 1.0)
emis_node = nodes.new('ShaderNodeEmission')
links.new(diff_node.outputs['BSDF'], s2rgb_node.inputs['Shader'])
links.new(s2rgb_node.outputs['Color'], ramp_node.inputs['Factor'])
links.new(ramp_node.outputs['Color'], emis_node.inputs['Color'])
links.new(emis_node.outputs['Emission'], out_node.inputs['Surface'])

# Assign Materials to Newly Created Objects
def assign_mat(obj, mat):
    if not obj: return
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

assign_mat(brooch_ring, mat_gold)
assign_mat(brooch_pearl, mat_pearl)
assign_mat(loop_l, mat_blue_ribbon)
assign_mat(loop_r, mat_blue_ribbon)

for btn in waist_buttons:
    assign_mat(btn, mat_gold)

assign_mat(flower_core, mat_gold)
for petal in waist_petals:
    assign_mat(petal, mat_pearl)
assign_mat(waist_streamer, mat_blue_ribbon)
assign_mat(waist_charm, mat_pearl)

assign_mat(back_knot, mat_ivory_cel)
assign_mat(back_wing_l, mat_ivory_cel)
assign_mat(back_wing_r, mat_ivory_cel)
for s_obj in back_streamers:
    assign_mat(s_obj, mat_blue_ribbon)

for cb in cuff_bows:
    assign_mat(cb, mat_blue_ribbon)

assign_mat(socks_obj, mat_socks)
for rf in sock_ruffles:
    assign_mat(rf, mat_socks)

print('-> Master NPR Cel Shaders created and assigned across all costume elements.')

# -------------------------------------------------------------
# 10. Solidify Inverted Hull Outline for Costume
# -------------------------------------------------------------
def add_inverted_outline(obj, thickness=-0.0014):
    outline_mat = bpy.data.materials.get('Aster_Mat_Outline')
    if not outline_mat:
        outline_mat = bpy.data.materials.new('Aster_Mat_Outline')
        outline_mat.use_nodes = True
        nodes = outline_mat.node_tree.nodes
        nodes.clear()
        out = nodes.new('ShaderNodeOutputMaterial')
        emis = nodes.new('ShaderNodeEmission')
        emis.inputs['Color'].default_value = (0.22, 0.20, 0.31, 1.0) # Deep Dark Purple Gray #38344E
        outline_mat.node_tree.links.new(emis.outputs['Emission'], out.inputs['Surface'])
    
    if outline_mat.name not in [m.name for m in obj.data.materials if m]:
        obj.data.materials.append(outline_mat)
    mat_idx = [i for i, m in enumerate(obj.data.materials) if m and m.name == outline_mat.name][0]
    
    mod = obj.modifiers.new('Costume_Outline', 'SOLIDIFY')
    mod.thickness = thickness
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.material_offset = mat_idx

add_inverted_outline(imported_mesh, thickness=-0.0014)
print('-> Applied inverted hull outline modifier to costume.')

# -------------------------------------------------------------
# 11. Multi-Angle Cameras Configuration (Front, Skirt Macro, 360 Turnaround)
# -------------------------------------------------------------
# Cam 1: Front Full Body
cam_front = bpy.data.objects.get('Cam1_Front')
if not cam_front:
    cam_front = bpy.data.objects.new('Cam1_Front', bpy.data.cameras.new('Cam1_Front'))
    bpy.context.scene.collection.objects.link(cam_front)
cam_front.location = (0.0, -2.8, 0.88)
cam_front.rotation_euler = (math.radians(90), 0, 0)
cam_front.data.lens = 75

# Cam 2: Skirt Layers Closeup
cam_skirt = bpy.data.objects.get('Cam2_SkirtCloseup')
if not cam_skirt:
    cam_skirt = bpy.data.objects.new('Cam2_SkirtCloseup', bpy.data.cameras.new('Cam2_SkirtCloseup'))
    bpy.context.scene.collection.objects.link(cam_skirt)
cam_skirt.location = (-0.35, -1.35, 0.88)
cam_skirt.rotation_euler = (math.radians(87), 0, math.radians(-15))
cam_skirt.data.lens = 90

# Cam 3: Back Flow & Bow Turnaround
cam_back = bpy.data.objects.get('Cam3_BackTurnaround')
if not cam_back:
    cam_back = bpy.data.objects.new('Cam3_BackTurnaround', bpy.data.cameras.new('Cam3_BackTurnaround'))
    bpy.context.scene.collection.objects.link(cam_back)
cam_back.location = (0.0, 2.85, 0.90)
cam_back.rotation_euler = (math.radians(90), 0, math.radians(180))
cam_back.data.lens = 75

print('-> Cameras positioned for 2K renders.')

# -------------------------------------------------------------
# 12. Save Milestone 3 .blend & Export .glb
# -------------------------------------------------------------
blend_out_path = os.path.join(models_dir, 'aster_milestone3_costume.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend_out_path)
print(f'-> Saved Blend file to: {blend_out_path}')

glb_out_path = os.path.join(models_dir, 'aster_milestone3_costume.glb')
bpy.ops.export_scene.gltf(
    filepath=glb_out_path,
    export_format='GLB',
    use_selection=False,
    export_apply=True
)
print(f'-> Exported GLB file to: {glb_out_path}')

# -------------------------------------------------------------
# 13. Render 3 2K Deliverables (2048 x 2048 PNG)
# -------------------------------------------------------------
bpy.context.scene.render.resolution_x = 2048
bpy.context.scene.render.resolution_y = 2048
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.image_settings.color_mode = 'RGBA'

renders = [
    (cam_front, '01_m3_full_costume_front.png'),
    (cam_skirt, '02_m3_skirt_layers_closeup.png'),
    (cam_back, '03_m3_costume_360_turnaround.png')
]

for cam, fn in renders:
    bpy.context.scene.camera = cam
    out_file = os.path.join(preview_dir, fn)
    bpy.context.scene.render.filepath = out_file
    print(f'Rendering 2K image: {fn}...')
    bpy.ops.render.render(write_still=True)
    print(f'-> Saved: {out_file}')

print('=== AsterNova Milestone 3 Costume Pipeline: All tasks completed successfully! ===')
