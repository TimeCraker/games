# AsterNova - Milestone 2: Multi-Layer Hair Assembly & NPR Shading Pipeline
# Character Technical Artist production script

import bpy
import addon_utils
import bmesh
import math
import os

addon_utils.enable('mmd_tools')

# 1. Load Milestone 1 Head & Body Master Scene
m1_blend = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\aster_milestone1_head_body.blend'
bpy.ops.wm.open_mainfile(filepath=m1_blend)

head_obj = bpy.data.objects['Head_Base']
body_obj = bpy.data.objects['Body_Base']

# 2. Import Columbina Back Flowing Hair (Layer 3)
columbina_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\columbina\columbina.pmx'
existing_objs = set(bpy.data.objects)
bpy.ops.mmd_tools.import_model(filepath=columbina_path, types={'MESH'})
c_obj = [o for o in bpy.data.objects if o not in existing_objs and o.type == 'MESH'][0]

bm = bmesh.new()
bm.from_mesh(c_obj.data)
# Keep only Mat 8: '髮' (grand long cascading hair flow)
del_faces = [f for f in bm.faces if f.material_index != 8]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')

# Remove Columbina forehead/mask attachment remnants (Y < -0.05, Z > 1.38)
remnant_faces = [f for f in bm.faces if f.calc_center_median().y < -0.05 and f.calc_center_median().z > 1.38]
bmesh.ops.delete(bm, geom=remnant_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(c_obj.data)
bm.free()
c_obj.data.update()
c_obj.name = "Hair_Layer3_BackFlow"

# 3. Import Furina Front Bangs & Crown (Layer 1 & Layer 2)
furina_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\furina\furina_1.pmx'
existing_objs = set(bpy.data.objects)
bpy.ops.mmd_tools.import_model(filepath=furina_path, types={'MESH'})
f_obj = [o for o in bpy.data.objects if o not in existing_objs and o.type == 'MESH'][0]

bm = bmesh.new()
bm.from_mesh(f_obj.data)
# Keep only Mat 10: '髮'
del_faces = [f for f in bm.faces if f.material_index != 10]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')

# Identify hair islands
visited = set()
islands = []
for f in bm.faces:
    if f in visited: continue
    isl, q = [], [f]
    visited.add(f)
    while q:
        curr = q.pop()
        isl.append(curr)
        for e in curr.edges:
            for lf in e.link_faces:
                if lf not in visited:
                    visited.add(lf); q.append(lf)
    islands.append(isl)

# Filter out oversized theatrical ahoge (Z > 1.60) and rear short curls (Y > 0.045)
del_islands = []
for isl in islands:
    max_z = max(v.co.z for f in isl for v in f.verts)
    center_y = sum(v.co.y for f in isl for v in f.verts) / sum(len(f.verts) for f in isl)
    if max_z > 1.60 or center_y > 0.045:
        del_islands.append(isl)

del_faces = [f for isl in del_islands for f in isl]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(f_obj.data)
bm.free()
f_obj.data.update()
# Align precisely with Head_Base top
f_obj.location.z = 0.012
f_obj.name = "Hair_Layer1_2_FrontBangs"

# 4. Import Aster Signature Accessories & Ahoge
glb_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_model.glb'
existing_objs = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb_path)
new_objs = [o for o in bpy.data.objects if o not in existing_objs]

keep_acc_names = [
    'Aster_Ahoge', 'Aster_HairFlower', 'Aster_HairFlower_Center',
    'Aster_HairLoop_1', 'Aster_HairLoop_2',
    'Aster_HairStreamer_1', 'Aster_HairStreamer_2',
    'Aster_RightHairPin', 'Aster_RightHairPin_Center',
    'Hair_Sphere_Normal_Proxy'
]

for o in new_objs:
    base_name = o.name.split('.')[0]
    if base_name not in keep_acc_names and o.type == 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)

# Adjust Aster Ahoge to plant naturally into skull crown
ahoge = bpy.data.objects.get('Aster_Ahoge')
if ahoge:
    ahoge.location.z -= 0.07
    ahoge.location.y -= 0.02

# Position floral hair accessories at left temple
flower_objs = ['Aster_HairFlower', 'Aster_HairFlower_Center', 'Aster_HairLoop_1', 'Aster_HairLoop_2', 'Aster_HairStreamer_1', 'Aster_HairStreamer_2']
for name in flower_objs:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.location.x += 0.02
        obj.location.y -= 0.03
        obj.location.z -= 0.02

proxy = bpy.data.objects.get('Hair_Sphere_Normal_Proxy')
if proxy:
    proxy.hide_render = True

# 5. Shaders: Master Pearl-White NPR Cel Hair Shader with Angel Ring
# Outline Material (Inverse Hull)
outline_mat = bpy.data.materials.new(name='Aster_Hair_Outline')
outline_mat.use_nodes = True
onodes = outline_mat.node_tree.nodes
onodes.clear()
o_out = onodes.new('ShaderNodeOutputMaterial')
o_em = onodes.new('ShaderNodeEmission')
o_em.inputs['Color'].default_value = (0.22, 0.20, 0.32, 1.0)
outline_mat.node_tree.links.new(o_em.outputs['Emission'], o_out.inputs['Surface'])
outline_mat.use_backface_culling = True

# Master Hair Material
hair_mat = bpy.data.materials.new(name='Aster_Hair_Master_NPR')
hair_mat.use_nodes = True
hnodes = hair_mat.node_tree.nodes
hlinks = hair_mat.node_tree.links
hnodes.clear()

h_out = hnodes.new('ShaderNodeOutputMaterial')

# A. Diffuse Cel Shading
diffuse = hnodes.new('ShaderNodeBsdfDiffuse')
s2rgb = hnodes.new('ShaderNodeShaderToRGB')
hlinks.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])

cel_ramp = hnodes.new('ShaderNodeValToRGB')
cel_ramp.color_ramp.interpolation = 'EASE'
# Shadow color: Soft Lavender Shadow (#bdb8d6)
cel_ramp.color_ramp.elements[0].position = 0.35
cel_ramp.color_ramp.elements[0].color = (0.55, 0.52, 0.68, 1.0)
# Lit color: Pearl White (#f2f4fc)
cel_ramp.color_ramp.elements[1].position = 0.55
cel_ramp.color_ramp.elements[1].color = (0.95, 0.96, 0.99, 1.0)
hlinks.new(s2rgb.outputs['Color'], cel_ramp.inputs['Fac'])

# B. Luminous Ice Cyan Angel Ring Band (Horizontal halo based on crown geometry)
geom = hnodes.new('ShaderNodeNewGeometry')
sep_xyz = hnodes.new('ShaderNodeSeparateXYZ')
hlinks.new(geom.outputs['Position'], sep_xyz.inputs['Vector'])

map_range = hnodes.new('ShaderNodeMapRange')
map_range.inputs['From Min'].default_value = 1.46
map_range.inputs['From Max'].default_value = 1.56
map_range.inputs['To Min'].default_value = 0.0
map_range.inputs['To Max'].default_value = 1.0
hlinks.new(sep_xyz.outputs['Z'], map_range.inputs['Value'])

halo_ramp = hnodes.new('ShaderNodeValToRGB')
halo_ramp.color_ramp.interpolation = 'CARDINAL'
halo_ramp.color_ramp.elements[0].position = 0.20
halo_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
el1 = halo_ramp.color_ramp.elements.new(0.42)
el1.color = (0.50, 0.80, 1.0, 1.0)
el2 = halo_ramp.color_ramp.elements.new(0.50)
el2.color = (0.75, 0.95, 1.0, 1.0) # Bright halo core
el3 = halo_ramp.color_ramp.elements.new(0.58)
el3.color = (0.50, 0.80, 1.0, 1.0)
halo_ramp.color_ramp.elements[3].position = 0.80
halo_ramp.color_ramp.elements[3].color = (0.0, 0.0, 0.0, 1.0)
hlinks.new(map_range.outputs['Result'], halo_ramp.inputs['Fac'])

# Modulate Angel Ring by light factor
halo_mask = hnodes.new('ShaderNodeMix')
halo_mask.data_type = 'RGBA'
halo_mask.blend_type = 'MULTIPLY'
halo_mask.inputs['Factor'].default_value = 1.0
hlinks.new(halo_ramp.outputs['Color'], halo_mask.inputs[6])
hlinks.new(s2rgb.outputs['Color'], halo_mask.inputs[7])

mix_angel = hnodes.new('ShaderNodeMix')
mix_angel.data_type = 'RGBA'
mix_angel.blend_type = 'ADD'
mix_angel.inputs['Factor'].default_value = 0.80
hlinks.new(cel_ramp.outputs['Color'], mix_angel.inputs[6])
hlinks.new(halo_mask.outputs[2], mix_angel.inputs[7])

# C. Grazing Angle Rim Light
fresnel = hnodes.new('ShaderNodeFresnel')
fresnel.inputs['IOR'].default_value = 1.25
fresnel_ramp = hnodes.new('ShaderNodeValToRGB')
fresnel_ramp.color_ramp.interpolation = 'EASE'
fresnel_ramp.color_ramp.elements[0].position = 0.65
fresnel_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
fresnel_ramp.color_ramp.elements[1].position = 0.95
fresnel_ramp.color_ramp.elements[1].color = (0.45, 0.65, 0.95, 1.0)
hlinks.new(fresnel.outputs['Fac'], fresnel_ramp.inputs['Fac'])

mix_rim = hnodes.new('ShaderNodeMix')
mix_rim.data_type = 'RGBA'
mix_rim.blend_type = 'ADD'
mix_rim.inputs['Factor'].default_value = 0.40
hlinks.new(mix_angel.outputs[2], mix_rim.inputs[6])
hlinks.new(fresnel_ramp.outputs['Color'], mix_rim.inputs[7])

h_em = hnodes.new('ShaderNodeEmission')
hlinks.new(mix_rim.outputs[2], h_em.inputs['Color'])
hlinks.new(h_em.outputs['Emission'], h_out.inputs['Surface'])

# Assign materials to hair objects
for h_obj in [f_obj, c_obj, ahoge]:
    if h_obj:
        h_obj.data.materials.clear()
        h_obj.data.materials.append(hair_mat)
        h_obj.data.materials.append(outline_mat)

# Add Inverse Hull Outline to Hair Meshes
for h_obj in [f_obj, c_obj]:
    solid_mod = h_obj.modifiers.new(name='HairOutline', type='SOLIDIFY')
    solid_mod.thickness = -0.0016
    solid_mod.offset = 1.0
    solid_mod.use_flip_normals = True
    solid_mod.material_offset = 1
    solid_mod.use_rim = False

# Add Hair Sphere Normal Transfer
if proxy:
    for h_obj in [f_obj, c_obj]:
        dt_mod = h_obj.modifiers.new(name='HairSphereNormalTransfer', type='DATA_TRANSFER')
        dt_mod.object = proxy
        dt_mod.use_loop_data = True
        dt_mod.data_types_loops = {'CUSTOM_NORMAL'}
        dt_mod.loop_mapping = 'POLYINTERP_NEAREST'
        dt_mod.mix_factor = 0.75

# D. Accessory Shaders: Champagne Gold, Pearl White, Celestial Blue
gold_mat = bpy.data.materials.new(name='Aster_Champagne_Gold_NPR')
gold_mat.use_nodes = True
gnodes = gold_mat.node_tree.nodes
gnodes.clear()
gout = gnodes.new('ShaderNodeOutputMaterial')
gem = gnodes.new('ShaderNodeEmission')
gem.inputs['Color'].default_value = (0.92, 0.78, 0.48, 1.0)
gold_mat.node_tree.links.new(gem.outputs['Emission'], gout.inputs['Surface'])

for g_name in ['Aster_HairFlower_Center', 'Aster_RightHairPin_Center']:
    o = bpy.data.objects.get(g_name)
    if o:
        o.data.materials.clear()
        o.data.materials.append(gold_mat)

pearl_mat = bpy.data.materials.new(name='Aster_Pearl_Petal_NPR')
pearl_mat.use_nodes = True
pnodes = pearl_mat.node_tree.nodes
pnodes.clear()
pout = pnodes.new('ShaderNodeOutputMaterial')
pem = pnodes.new('ShaderNodeEmission')
pem.inputs['Color'].default_value = (0.96, 0.97, 1.0, 1.0)
pearl_mat.node_tree.links.new(pem.outputs['Emission'], pout.inputs['Surface'])

for p_name in ['Aster_HairFlower', 'Aster_RightHairPin']:
    o = bpy.data.objects.get(p_name)
    if o:
        o.data.materials.clear()
        o.data.materials.append(pearl_mat)

ribbon_mat = bpy.data.materials.new(name='Aster_Ribbon_SkyBlue_NPR')
ribbon_mat.use_nodes = True
rnodes = ribbon_mat.node_tree.nodes
rnodes.clear()
rout = rnodes.new('ShaderNodeOutputMaterial')
rem = rnodes.new('ShaderNodeEmission')
rem.inputs['Color'].default_value = (0.50, 0.74, 0.96, 1.0)
ribbon_mat.node_tree.links.new(rem.outputs['Emission'], rout.inputs['Surface'])

for r_name in ['Aster_HairLoop_1', 'Aster_HairLoop_2', 'Aster_HairStreamer_1', 'Aster_HairStreamer_2']:
    o = bpy.data.objects.get(r_name)
    if o:
        o.data.materials.clear()
        o.data.materials.append(ribbon_mat)

# 6. Save Milestone 2 Master Model & Export GLB
m2_blend = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\aster_milestone2_hair.blend'
bpy.ops.wm.save_as_mainfile(filepath=m2_blend)
print(f"[Pipeline] Milestone 2 Blend saved: {m2_blend}")

m2_glb = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\aster_milestone2_hair.glb'
bpy.ops.export_scene.gltf(
    filepath=m2_glb,
    export_format='GLB',
    use_selection=False,
    export_apply=False
)
print(f"[Pipeline] Milestone 2 GLB exported: {m2_glb}")

# 7. Render 3 Studio Verification 2K Renders
render_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews\milestone2'
os.makedirs(render_dir, exist_ok=True)

bpy.context.scene.render.resolution_x = 2048
bpy.context.scene.render.resolution_y = 2048
bpy.context.scene.world.color = (0.05, 0.05, 0.08)

key_light = bpy.data.objects.get('KeyLight')
if not key_light:
    kdata = bpy.data.lights.new('KeyLight', type='SUN')
    key_light = bpy.data.objects.new('KeyLight', kdata)
    bpy.context.scene.collection.objects.link(key_light)
key_light.data.energy = 1.0

fill_light = bpy.data.objects.get('FillLight')
if not fill_light:
    fdata = bpy.data.lights.new('FillLight', type='SUN')
    fill_light = bpy.data.objects.new('FillLight', fdata)
    bpy.context.scene.collection.objects.link(fill_light)
fill_light.data.energy = 0.25
fill_light.data.color = (0.75, 0.85, 1.0)
fill_light.rotation_euler = (math.radians(30), math.radians(-30), math.radians(-45))

cam = bpy.data.objects.get('Camera')
if not cam:
    cdata = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cdata)
    bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

# View 1: 01_m2_hair_front_view.png (Front Hair & Face Alignment)
key_light.rotation_euler = (math.radians(45), math.radians(15), math.radians(35))
cam.location = (0, -0.65, 1.48)
cam.rotation_euler = (math.radians(90), 0, 0)
cam.data.lens = 70
p1 = os.path.join(render_dir, '01_m2_hair_front_view.png')
bpy.context.scene.render.filepath = p1
bpy.ops.render.render(write_still=True)
print(f"[Pipeline] Render 1 Front View: {os.path.exists(p1)} -> {p1}")

# View 2: 02_m2_hair_back_flow.png (Back Cascading Waves & Ribbon Accessories)
key_light.rotation_euler = (math.radians(45), math.radians(-15), math.radians(145))
cam.location = (0, 0.9, 1.35)
cam.rotation_euler = (math.radians(90), 0, math.radians(180))
cam.data.lens = 65
p2 = os.path.join(render_dir, '02_m2_hair_back_flow.png')
bpy.context.scene.render.filepath = p2
bpy.ops.render.render(write_still=True)
print(f"[Pipeline] Render 2 Back Flow: {os.path.exists(p2)} -> {p2}")

# View 3: 03_m2_hair_normal_smoothness.png (90-deg Sidelight, Angel Ring & Normal Smoothness)
key_light.rotation_euler = (math.radians(25), math.radians(20), math.radians(85))
cam.location = (-0.6, -0.5, 1.48)
cam.rotation_euler = (math.radians(90), 0, math.radians(-50))
cam.data.lens = 70
p3 = os.path.join(render_dir, '03_m2_hair_normal_smoothness.png')
bpy.context.scene.render.filepath = p3
bpy.ops.render.render(write_still=True)
print(f"[Pipeline] Render 3 Sidelight / Normal Smoothness: {os.path.exists(p3)} -> {p3}")

print("MILESTONE 2 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
