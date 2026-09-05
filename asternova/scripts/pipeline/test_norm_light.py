import bpy, addon_utils, bmesh, math, os

addon_utils.enable('mmd_tools')

m1_blend = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\aster_milestone1_head_body.blend'
bpy.ops.wm.open_mainfile(filepath=m1_blend)

# 1. Columbina Back Hair
columbina_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\columbina\columbina.pmx'
existing_objs = set(bpy.data.objects)
bpy.ops.mmd_tools.import_model(filepath=columbina_path, types={'MESH'})
c_obj = [o for o in bpy.data.objects if o not in existing_objs and o.type == 'MESH'][0]

bm = bmesh.new()
bm.from_mesh(c_obj.data)
del_faces = [f for f in bm.faces if f.material_index != 8]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
remnant_faces = [f for f in bm.faces if f.calc_center_median().y < -0.05 and f.calc_center_median().z > 1.38]
bmesh.ops.delete(bm, geom=remnant_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(c_obj.data)
bm.free()
c_obj.data.update()
c_obj.name = "Hair_Layer3_Back"

# 2. Furina Front Hair & Crown
furina_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\furina\furina_1.pmx'
existing_objs = set(bpy.data.objects)
bpy.ops.mmd_tools.import_model(filepath=furina_path, types={'MESH'})
f_obj = [o for o in bpy.data.objects if o not in existing_objs and o.type == 'MESH'][0]

bm = bmesh.new()
bm.from_mesh(f_obj.data)
del_faces = [f for f in bm.faces if f.material_index != 10]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')

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
f_obj.location.z = 0.012
f_obj.name = "Hair_Layer1_2_Front"

# 3. Aster Accessories & Ahoge
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

ahoge = bpy.data.objects.get('Aster_Ahoge')
if ahoge:
    ahoge.location.z -= 0.07
    ahoge.location.y -= 0.02

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

# 4. Master NPR Cel Shaders
outline_mat = bpy.data.materials.new(name='Aster_Hair_Outline')
outline_mat.use_nodes = True
nodes = outline_mat.node_tree.nodes
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial')
em = nodes.new('ShaderNodeEmission')
em.inputs['Color'].default_value = (0.22, 0.20, 0.32, 1.0)
outline_mat.node_tree.links.new(em.outputs['Emission'], out.inputs['Surface'])
outline_mat.use_backface_culling = True

hair_mat = bpy.data.materials.new(name='Aster_Hair_Master_NPR')
hair_mat.use_nodes = True
nodes = hair_mat.node_tree.nodes
links = hair_mat.node_tree.links
nodes.clear()

out = nodes.new('ShaderNodeOutputMaterial')

# 1) Diffuse Cel Shading
diffuse = nodes.new('ShaderNodeBsdfDiffuse')
s2rgb = nodes.new('ShaderNodeShaderToRGB')
links.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])

cel_ramp = nodes.new('ShaderNodeValToRGB')
cel_ramp.color_ramp.interpolation = 'EASE'
# Shadow color: Rich Lavender Shadow (#8882a8)
cel_ramp.color_ramp.elements[0].position = 0.35
cel_ramp.color_ramp.elements[0].color = (0.55, 0.52, 0.68, 1.0)
# Lit color: Pearl White (#f2f4fc)
cel_ramp.color_ramp.elements[1].position = 0.55
cel_ramp.color_ramp.elements[1].color = (0.95, 0.96, 0.99, 1.0)
links.new(s2rgb.outputs['Color'], cel_ramp.inputs['Fac'])

# 2) Angel Ring (Halo)
glossy = nodes.new('ShaderNodeBsdfGlossy')
glossy.inputs['Roughness'].default_value = 0.12
s2rgb_gloss = nodes.new('ShaderNodeShaderToRGB')
links.new(glossy.outputs['BSDF'], s2rgb_gloss.inputs['Shader'])

angel_ramp = nodes.new('ShaderNodeValToRGB')
angel_ramp.color_ramp.interpolation = 'EASE'
angel_ramp.color_ramp.elements[0].position = 0.30
angel_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
# Luminous Ice Cyan-Blue Angel Ring
angel_ramp.color_ramp.elements[1].position = 0.65
angel_ramp.color_ramp.elements[1].color = (0.65, 0.85, 1.0, 1.0)
links.new(s2rgb_gloss.outputs['Color'], angel_ramp.inputs['Fac'])

# Modulate angel ring by light
mix_angel_mask = nodes.new('ShaderNodeMix')
mix_angel_mask.data_type = 'RGBA'
mix_angel_mask.blend_type = 'MULTIPLY'
mix_angel_mask.inputs['Factor'].default_value = 1.0
links.new(angel_ramp.outputs['Color'], mix_angel_mask.inputs[6])
links.new(s2rgb.outputs['Color'], mix_angel_mask.inputs[7])

# Add Angel Ring onto Cel Shading
mix_angel = nodes.new('ShaderNodeMix')
mix_angel.data_type = 'RGBA'
mix_angel.blend_type = 'ADD'
mix_angel.inputs['Factor'].default_value = 0.80
links.new(cel_ramp.outputs['Color'], mix_angel.inputs[6])
links.new(mix_angel_mask.outputs[2], mix_angel.inputs[7])

# Subtle grazing Rim
fresnel = nodes.new('ShaderNodeFresnel')
fresnel.inputs['IOR'].default_value = 1.25
fresnel_ramp = nodes.new('ShaderNodeValToRGB')
fresnel_ramp.color_ramp.interpolation = 'EASE'
fresnel_ramp.color_ramp.elements[0].position = 0.65
fresnel_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
fresnel_ramp.color_ramp.elements[1].position = 0.95
fresnel_ramp.color_ramp.elements[1].color = (0.45, 0.65, 0.95, 1.0)
links.new(fresnel.outputs['Fac'], fresnel_ramp.inputs['Fac'])

mix_rim = nodes.new('ShaderNodeMix')
mix_rim.data_type = 'RGBA'
mix_rim.blend_type = 'ADD'
mix_rim.inputs['Factor'].default_value = 0.40
links.new(mix_angel.outputs[2], mix_rim.inputs[6])
links.new(fresnel_ramp.outputs['Color'], mix_rim.inputs[7])

emission = nodes.new('ShaderNodeEmission')
links.new(mix_rim.outputs[2], emission.inputs['Color'])
links.new(emission.outputs['Emission'], out.inputs['Surface'])

for h_obj in [f_obj, c_obj, ahoge]:
    if h_obj:
        h_obj.data.materials.clear()
        h_obj.data.materials.append(hair_mat)
        h_obj.data.materials.append(outline_mat)

for h_obj in [f_obj, c_obj]:
    solid_mod = h_obj.modifiers.new(name='HairOutline', type='SOLIDIFY')
    solid_mod.thickness = -0.0016
    solid_mod.offset = 1.0
    solid_mod.use_flip_normals = True
    solid_mod.material_offset = 1
    solid_mod.use_rim = False

if proxy:
    for h_obj in [f_obj, c_obj]:
        dt_mod = h_obj.modifiers.new(name='HairSphereNormalTransfer', type='DATA_TRANSFER')
        dt_mod.object = proxy
        dt_mod.use_loop_data = True
        dt_mod.data_types_loops = {'CUSTOM_NORMAL'}
        dt_mod.loop_mapping = 'POLYINTERP_NEAREST'
        dt_mod.mix_factor = 0.75

# Accessory Materials
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

# 5. Lighting: Normalised 1.0 Key Energy for Exact Cel Ramp Response
bpy.context.scene.world.color = (0.05, 0.05, 0.08)

key_light = bpy.data.objects.get('KeyLight')
if not key_light:
    kdata = bpy.data.lights.new('KeyLight', type='SUN')
    key_light = bpy.data.objects.new('KeyLight', kdata)
    bpy.context.scene.collection.objects.link(key_light)
key_light.data.energy = 1.0
key_light.rotation_euler = (math.radians(45), math.radians(15), math.radians(35))

fill_light = bpy.data.objects.get('FillLight')
if not fill_light:
    fdata = bpy.data.lights.new('FillLight', type='SUN')
    fill_light = bpy.data.objects.new('FillLight', fdata)
    bpy.context.scene.collection.objects.link(fill_light)
fill_light.data.energy = 0.25
fill_light.data.color = (0.75, 0.85, 1.0)
fill_light.rotation_euler = (math.radians(30), math.radians(-30), math.radians(-45))

out_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews'
bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024

cam = bpy.data.objects.get('Camera')
if not cam:
    cdata = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cdata)
    bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

# View 3: Side strong light (90 deg sidelight)
key_light.rotation_euler = (math.radians(25), math.radians(20), math.radians(85))
cam.location = (-0.6, -0.5, 1.48)
cam.rotation_euler = (math.radians(90), 0, math.radians(-50))
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_norm_side.png')
bpy.ops.render.render(write_still=True)
print("TEST NORM SIDE RENDERED")
