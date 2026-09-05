# AsterNova - Milestone 1: 8.5 Head-to-Body Base & NPR Face Pipeline
import bpy, addon_utils, bmesh, os, mathutils

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m, do_unlink=True)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat, do_unlink=True)

addon_utils.enable('mmd_tools')

def find_mat_idx(obj, base_name):
    for i, m in enumerate(obj.data.materials):
        if m.name.split('.')[0] == base_name:
            return i
    return -1

def find_mat(obj, base_name):
    for m in obj.data.materials:
        if m.name.split('.')[0] == base_name:
            return m
    return None

# 1. Import Columbina Body Base (8.61 Head-to-Body Ratio)
columbina_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\columbina\columbina.pmx'
bpy.ops.mmd_tools.import_model(filepath=columbina_path, types={'MESH'})
body_obj = bpy.data.objects['columbina_mesh']
body_obj.name = 'Body_Base'

# Strip cloak, coat, accessories, face/hair from Columbina, keeping body base & choker
keep_body_keywords = ['肌', '体', '鞋']
del_body_mats = []
for i, m in enumerate(body_obj.data.materials):
    base = m.name.split('.')[0]
    if not any(k in base for k in keep_body_keywords):
        del_body_mats.append(i)

bm = bmesh.new()
bm.from_mesh(body_obj.data)
del_faces = [f for f in bm.faces if f.material_index in del_body_mats]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(body_obj.data)
bm.free()
body_obj.data.update()

# 2. Import Layla Head Base (Quad Edge-Loops Facial Topology)
layla_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\layla\layla.pmx'
bpy.ops.mmd_tools.import_model(filepath=layla_path, types={'MESH'})
head_obj = bpy.data.objects['layla_mesh']
head_obj.name = 'Head_Base'

keep_head_keywords = ['颜', '颜2', '白目', '目', '星目', '口舌', '齿', '眉', '睫', '二重']
del_head_mats = []
for i, m in enumerate(head_obj.data.materials):
    base = m.name.split('.')[0]
    if not any(k == base for k in keep_head_keywords):
        del_head_mats.append(i)

bm = bmesh.new()
bm.from_mesh(head_obj.data)
del_faces = [f for f in bm.faces if f.material_index in del_head_mats]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')

# Align Head to Columbina neck socket
dy = -0.0788 - (-0.0633)
dz = 1.3345 - 1.3096
for v in bm.verts:
    v.co.y += dy
    v.co.z += dz

# Offset Star Highlights forward in Y (CRITICAL: use set of unique vertices to avoid duplicate shift!)
idx_star = find_mat_idx(head_obj, '星目')
idx_eye = find_mat_idx(head_obj, '目')
if idx_star >= 0 and idx_eye >= 0:
    eye_front_y = min(f.calc_center_bounds().y for f in bm.faces if f.material_index == idx_eye)
    star_curr_y = sum(f.calc_center_bounds().y for f in bm.faces if f.material_index == idx_star) / 64
    star_shift_y = eye_front_y - 0.0018 - star_curr_y
    star_verts = set(v for f in bm.faces if f.material_index == idx_star for v in f.verts)
    for v in star_verts:
        v.co.y += star_shift_y

# Remap Eye Iris UVs to [0, 1]^2
eye_faces = [f for f in bm.faces if f.material_index == idx_eye]
uv_lay = bm.loops.layers.uv.active

left_eye = [f for f in eye_faces if f.calc_center_bounds().x > 0]
right_eye = [f for f in eye_faces if f.calc_center_bounds().x < 0]

def remap_eye(faces):
    if not faces:
        return
    uvs = [l[uv_lay].uv for f in faces for l in f.loops]
    min_x, max_x = min(u.x for u in uvs), max(u.x for u in uvs)
    min_y, max_y = min(u.y for u in uvs), max(u.y for u in uvs)
    w, h = max_x - min_x, max_y - min_y
    for f in faces:
        for l in f.loops:
            u = (l[uv_lay].uv.x - min_x) / w
            v = (l[uv_lay].uv.y - min_y) / h
            l[uv_lay].uv = mathutils.Vector((u, v))

remap_eye(left_eye)
remap_eye(right_eye)

bm.to_mesh(head_obj.data)
bm.free()
head_obj.data.update()

# 3. Shaders Setup
# Face NPR
mat_face = find_mat(head_obj, '颜')
if mat_face:
    mat_face.use_nodes = True
    nodes = mat_face.node_tree.nodes
    links = mat_face.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (800, 0)
    tex_face = nodes.new('ShaderNodeTexImage')
    tex_face.image = bpy.data.images.load(r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\layla\tex\颜.png')
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    s2rgb = nodes.new('ShaderNodeShaderToRGB')
    links.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'EASE'
    ramp.color_ramp.elements[0].position = 0.44
    ramp.color_ramp.elements[0].color = (0.90, 0.85, 0.87, 1.0)
    ramp.color_ramp.elements[1].position = 0.52
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    links.new(s2rgb.outputs['Color'], ramp.inputs['Fac'])
    mix = nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    links.new(tex_face.outputs['Color'], mix.inputs[6])
    links.new(ramp.outputs['Color'], mix.inputs[7])
    em_face = nodes.new('ShaderNodeEmission')
    em_face.inputs['Strength'].default_value = 1.0
    links.new(mix.outputs[2], em_face.inputs['Color'])
    links.new(em_face.outputs['Emission'], out.inputs['Surface'])

# Eye Iris
mat_eye = find_mat(head_obj, '目')
if mat_eye:
    mat_eye.use_nodes = True
    nodes = mat_eye.node_tree.nodes
    links = mat_eye.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    tex_eye = nodes.new('ShaderNodeTexImage')
    tex_eye.image = bpy.data.images.load(r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews\columbina_eye_view.png')
    hsv = nodes.new('ShaderNodeHueSaturation')
    hsv.inputs['Hue'].default_value = 0.30
    hsv.inputs['Saturation'].default_value = 1.40
    hsv.inputs['Value'].default_value = 1.08
    links.new(tex_eye.outputs['Color'], hsv.inputs['Color'])
    em_eye = nodes.new('ShaderNodeEmission')
    em_eye.inputs['Strength'].default_value = 1.20
    links.new(hsv.outputs['Color'], em_eye.inputs['Color'])
    links.new(em_eye.outputs['Emission'], out.inputs['Surface'])

# Star Highlight
mat_star = find_mat(head_obj, '星目')
if mat_star:
    mat_star.use_nodes = True
    nodes = mat_star.node_tree.nodes
    links = mat_star.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    em_star = nodes.new('ShaderNodeEmission')
    em_star.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    em_star.inputs['Strength'].default_value = 4.5
    links.new(em_star.outputs['Emission'], out.inputs['Surface'])

# Eyebrows & Lashes
for m in head_obj.data.materials:
    base = m.name.split('.')[0]
    if any(k in base for k in ['眉', '睫', '二重']):
        m.use_nodes = True
        nodes = m.node_tree.nodes
        links = m.node_tree.links
        nodes.clear()
        out = nodes.new('ShaderNodeOutputMaterial')
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\layla\tex\颜.png')
        if '眉' in base:
            mix_color = nodes.new('ShaderNodeMix')
            mix_color.data_type = 'RGBA'
            mix_color.blend_type = 'COLOR'
            mix_color.inputs['Factor'].default_value = 0.90
            mix_color.inputs[7].default_value = (0.55, 0.60, 0.70, 1.0)
            links.new(tex.outputs['Color'], mix_color.inputs[6])
            em = nodes.new('ShaderNodeEmission')
            em.inputs['Strength'].default_value = 1.0
            links.new(mix_color.outputs[2], em.inputs['Color'])
        else:
            em = nodes.new('ShaderNodeEmission')
            em.inputs['Strength'].default_value = 1.0
            links.new(tex.outputs['Color'], em.inputs['Color'])
        trans = nodes.new('ShaderNodeBsdfTransparent')
        mix_sh = nodes.new('ShaderNodeMixShader')
        links.new(tex.outputs['Alpha'], mix_sh.inputs['Fac'])
        links.new(trans.outputs['BSDF'], mix_sh.inputs[1])
        links.new(em.outputs['Emission'], mix_sh.inputs[2])
        links.new(mix_sh.outputs['Shader'], out.inputs['Surface'])
        if hasattr(m, 'blend_method'):
            m.blend_method = 'CLIP'

# Sclera
mat_sclera = find_mat(head_obj, '白目')
if mat_sclera:
    mat_sclera.use_nodes = True
    nodes = mat_sclera.node_tree.nodes
    links = mat_sclera.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    em = nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.97, 0.98, 1.0, 1.0)
    em.inputs['Strength'].default_value = 1.0
    links.new(em.outputs['Emission'], out.inputs['Surface'])

# Mouth & Teeth
for m in head_obj.data.materials:
    base = m.name.split('.')[0]
    if any(k in base for k in ['口舌', '齿']):
        m.use_nodes = True
        nodes = m.node_tree.nodes
        links = m.node_tree.links
        nodes.clear()
        out = nodes.new('ShaderNodeOutputMaterial')
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\layla\tex\颜.png')
        em = nodes.new('ShaderNodeEmission')
        em.inputs['Strength'].default_value = 1.0
        links.new(tex.outputs['Color'], em.inputs['Color'])
        links.new(em.outputs['Emission'], out.inputs['Surface'])

# Body Skin, Tights & Choker
for m in body_obj.data.materials:
    base = m.name.split('.')[0]
    if any(k in base for k in ['肌', '体', '鞋']):
        m.use_nodes = True
        nodes = m.node_tree.nodes
        links = m.node_tree.links
        img_node = [n for n in nodes if n.type == 'TEX_IMAGE' and n.image]
        if img_node:
            img = img_node[0].image
            nodes.clear()
            out = nodes.new('ShaderNodeOutputMaterial')
            tex = nodes.new('ShaderNodeTexImage')
            tex.image = img
            diffuse = nodes.new('ShaderNodeBsdfDiffuse')
            s2rgb = nodes.new('ShaderNodeShaderToRGB')
            links.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])
            ramp = nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.interpolation = 'EASE'
            ramp.color_ramp.elements[0].position = 0.45
            ramp.color_ramp.elements[0].color = (0.88, 0.85, 0.88, 1.0)
            ramp.color_ramp.elements[1].position = 0.52
            ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
            links.new(s2rgb.outputs['Color'], ramp.inputs['Fac'])
            mix = nodes.new('ShaderNodeMix')
            mix.data_type = 'RGBA'
            mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            links.new(tex.outputs['Color'], mix.inputs[6])
            links.new(ramp.outputs['Color'], mix.inputs[7])
            em = nodes.new('ShaderNodeEmission')
            em.inputs['Strength'].default_value = 1.0
            links.new(mix.outputs[2], em.inputs['Color'])
            links.new(em.outputs['Emission'], out.inputs['Surface'])

# 4. Lighting & Environment
bpy.context.scene.world.color = (0.75, 0.77, 0.82)

key_data = bpy.data.lights.new('KeyLight', type='SUN')
key_data.energy = 2.4
key_obj = bpy.data.objects.new('KeyLight', key_data)
bpy.context.scene.collection.objects.link(key_obj)
key_obj.rotation_euler = (0.5, 0.3, 0.6)

fill_data = bpy.data.lights.new('FillLight', type='SUN')
fill_data.energy = 1.2
fill_data.color = (0.88, 0.92, 1.0)
fill_obj = bpy.data.objects.new('FillLight', fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.rotation_euler = (0.4, -0.4, -0.5)

rim_data = bpy.data.lights.new('RimLight', type='SUN')
rim_data.energy = 1.8
rim_obj = bpy.data.objects.new('RimLight', rim_data)
bpy.context.scene.collection.objects.link(rim_obj)
rim_obj.rotation_euler = (-0.8, 0.0, 2.8)

out_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews\milestone1'
os.makedirs(out_dir, exist_ok=True)

# Render 1: Front Full Body
cam1_data = bpy.data.cameras.new('Cam1_Front')
cam1_data.lens = 52
cam1_obj = bpy.data.objects.new('Cam1_Front', cam1_data)
bpy.context.scene.collection.objects.link(cam1_obj)
bpy.context.scene.camera = cam1_obj
cam1_obj.location = (0.0, -2.85, 0.82)
cam1_obj.rotation_euler = (1.5708, 0, 0)

bpy.context.scene.render.resolution_x = 2048
bpy.context.scene.render.resolution_y = 2048
p1 = os.path.join(out_dir, '01_m1_body_silhouette_front.png')
bpy.context.scene.render.filepath = p1
bpy.ops.render.render(write_still=True)
print('[Pipeline] Render 1 Front Body:', os.path.exists(p1), p1)

# Render 2: 3/4 Face Closeup
cam2_data = bpy.data.cameras.new('Cam2_34Face')
cam2_data.lens = 85
cam2_obj = bpy.data.objects.new('Cam2_34Face', cam2_data)
bpy.context.scene.collection.objects.link(cam2_obj)
bpy.context.scene.camera = cam2_obj
cam2_obj.location = (0.28, -0.66, 1.435)
cam2_obj.rotation_euler = (1.52, 0.0, 0.38)

bpy.context.scene.render.resolution_x = 2048
bpy.context.scene.render.resolution_y = 2048
p2 = os.path.join(out_dir, '02_m1_face_three_quarter.png')
bpy.context.scene.render.filepath = p2
bpy.ops.render.render(write_still=True)
print('[Pipeline] Render 2 3/4 Face:', os.path.exists(p2), p2)

# Render 3: Eye Macro Closeup (Lens 85mm at Y=-0.46m for perfect framing of both eyes, nose bridge and eyebrows)
cam3_data = bpy.data.cameras.new('Cam3_Eye')
cam3_data.lens = 85
cam3_obj = bpy.data.objects.new('Cam3_Eye', cam3_data)
bpy.context.scene.collection.objects.link(cam3_obj)
bpy.context.scene.camera = cam3_obj
cam3_obj.location = (0.0, -0.46, 1.425)
cam3_obj.rotation_euler = (1.5708, 0, 0)

bpy.context.scene.render.resolution_x = 2048
bpy.context.scene.render.resolution_y = 2048
p3 = os.path.join(out_dir, '03_m1_eyes_closeup.png')
bpy.context.scene.render.filepath = p3
bpy.ops.render.render(write_still=True)
print('[Pipeline] Render 3 Eye Macro:', os.path.exists(p3), p3)

# Save master .blend file
blend_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models'
os.makedirs(blend_dir, exist_ok=True)
blend_path = os.path.join(blend_dir, 'aster_milestone1_head_body.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print('[Pipeline] Saved Master Blend:', os.path.exists(blend_path), blend_path)
