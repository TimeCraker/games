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

# 4. Hair Shaders with Texture Texture-Luminance Tinting + Cel Shadowing
# Create Hair Outline Material (Inverse Hull)
outline_mat = bpy.data.materials.new(name='Aster_Hair_Outline')
outline_mat.use_nodes = True
nodes = outline_mat.node_tree.nodes
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial')
em = nodes.new('ShaderNodeEmission')
# Dark lavender-charcoal outline color
em.inputs['Color'].default_value = (0.28, 0.26, 0.35, 1.0)
outline_mat.node_tree.links.new(em.outputs['Emission'], out.inputs['Surface'])
outline_mat.use_backface_culling = True


# Create Hair Master NPR Shader
hair_mat = bpy.data.materials.new(name='Aster_Hair_Master_NPR')
hair_mat.use_nodes = True
nodes = hair_mat.node_tree.nodes
links = hair_mat.node_tree.links
nodes.clear()

out = nodes.new('ShaderNodeOutputMaterial')

# Diffuse Cel Shading
diffuse = nodes.new('ShaderNodeBsdfDiffuse')
s2rgb = nodes.new('ShaderNodeShaderToRGB')
links.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])

cel_ramp = nodes.new('ShaderNodeValToRGB')
cel_ramp.color_ramp.interpolation = 'EASE'
# Shadow color: Elegant lavender shadow
cel_ramp.color_ramp.elements[0].position = 0.46
cel_ramp.color_ramp.elements[0].color = (0.72, 0.69, 0.82, 1.0)
# Lit color: Pearl White (#f2f4fc)
cel_ramp.color_ramp.elements[1].position = 0.54
cel_ramp.color_ramp.elements[1].color = (0.95, 0.96, 0.99, 1.0)
links.new(s2rgb.outputs['Color'], cel_ramp.inputs['Fac'])

# Glossy Angel Ring (Halo highlight band)
glossy = nodes.new('ShaderNodeBsdfGlossy')
glossy.inputs['Roughness'].default_value = 0.16
s2rgb_gloss = nodes.new('ShaderNodeShaderToRGB')
links.new(glossy.outputs['BSDF'], s2rgb_gloss.inputs['Shader'])

angel_ramp = nodes.new('ShaderNodeValToRGB')
angel_ramp.color_ramp.interpolation = 'EASE'
angel_ramp.color_ramp.elements[0].position = 0.58
angel_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
# Cool Ice Cyan-Blue Angel Ring
angel_ramp.color_ramp.elements[1].position = 0.80
angel_ramp.color_ramp.elements[1].color = (0.60, 0.80, 1.0, 1.0)
links.new(s2rgb_gloss.outputs['Color'], angel_ramp.inputs['Fac'])

# Add Angel Ring to Cel Shading
mix_angel = nodes.new('ShaderNodeMix')
mix_angel.data_type = 'RGBA'
mix_angel.blend_type = 'ADD'
mix_angel.inputs['Factor'].default_value = 0.70
links.new(cel_ramp.outputs['Color'], mix_angel.inputs[6])
links.new(angel_ramp.outputs['Color'], mix_angel.inputs[7])

# Subtle grazing Rim
fresnel = nodes.new('ShaderNodeFresnel')
fresnel.inputs['IOR'].default_value = 1.30
fresnel_ramp = nodes.new('ShaderNodeValToRGB')
fresnel_ramp.color_ramp.interpolation = 'EASE'
fresnel_ramp.color_ramp.elements[0].position = 0.72
fresnel_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
fresnel_ramp.color_ramp.elements[1].position = 0.96
fresnel_ramp.color_ramp.elements[1].color = (0.50, 0.70, 0.95, 1.0)
links.new(fresnel.outputs['Fac'], fresnel_ramp.inputs['Fac'])

mix_rim = nodes.new('ShaderNodeMix')
mix_rim.data_type = 'RGBA'
mix_rim.blend_type = 'ADD'
mix_rim.inputs['Factor'].default_value = 0.50
links.new(mix_angel.outputs[2], mix_rim.inputs[6])
links.new(fresnel_ramp.outputs['Color'], mix_rim.inputs[7])

emission = nodes.new('ShaderNodeEmission')
links.new(mix_rim.outputs[2], emission.inputs['Color'])
links.new(emission.outputs['Emission'], out.inputs['Surface'])

# Assign hair shader
for h_obj in [f_obj, c_obj, ahoge]:
    if h_obj:
        h_obj.data.materials.clear()
        h_obj.data.materials.append(hair_mat)
        h_obj.data.materials.append(outline_mat)

# Add Inverse Hull Outline to Hair Meshes
for h_obj in [f_obj, c_obj]:
    solid_mod = h_obj.modifiers.new(name='HairOutline', type='SOLIDIFY')
    solid_mod.thickness = -0.0018
    solid_mod.offset = 1.0
    solid_mod.use_flip_normals = True
    solid_mod.material_offset = 1 # use outline_mat
    solid_mod.use_rim = False

# Add Normal Transfer
if proxy:
    for h_obj in [f_obj, c_obj]:
        dt_mod = h_obj.modifiers.new(name='HairSphereNormalTransfer', type='DATA_TRANSFER')
        dt_mod.object = proxy
        dt_mod.use_loop_data = True
        dt_mod.data_types_loops = {'CUSTOM_NORMAL'}
        dt_mod.loop_mapping = 'POLYINTERP_NEAREST'
        dt_mod.mix_factor = 0.75

# 5. Lighting Setup
bpy.context.scene.world.color = (0.75, 0.77, 0.82)

key_light = bpy.data.objects.get('KeyLight')
if not key_light:
    kdata = bpy.data.lights.new('KeyLight', type='SUN')
    key_light = bpy.data.objects.new('KeyLight', kdata)
    bpy.context.scene.collection.objects.link(key_light)
key_light.data.energy = 2.4
key_light.rotation_euler = (0.5, 0.3, 0.6)

fill_light = bpy.data.objects.get('FillLight')
if not fill_light:
    fdata = bpy.data.lights.new('FillLight', type='SUN')
    fill_light = bpy.data.objects.new('FillLight', fdata)
    bpy.context.scene.collection.objects.link(fill_light)
fill_light.data.energy = 1.2
fill_light.data.color = (0.88, 0.92, 1.0)
fill_light.rotation_euler = (0.4, -0.4, -0.5)

# Render test images
out_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews'
bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024

cam = bpy.data.objects.get('Camera')
if not cam:
    cdata = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cdata)
    bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

# Front view
cam.location = (0, -0.65, 1.48)
cam.rotation_euler = (math.radians(90), 0, 0)
cam.data.lens = 70
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_enhanced_front.png')
bpy.ops.render.render(write_still=True)

# Back view
cam.location = (0, 0.9, 1.35)
cam.rotation_euler = (math.radians(90), 0, math.radians(180))
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_enhanced_back.png')
bpy.ops.render.render(write_still=True)

# 3/4 Side view
cam.location = (-0.6, -0.5, 1.48)
cam.rotation_euler = (math.radians(90), 0, math.radians(-50))
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_enhanced_side.png')
bpy.ops.render.render(write_still=True)

print("ENHANCED TESTS RENDERED")
