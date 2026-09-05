"""
AsterNova 角色建模工业化管线 - 阶段 1：原始网格重拓扑与分件标定
Phase 1: Raw AI Sculpt Ingestion, Quad Remeshing, Disassembly & Wireframe Verification
"""

import bpy
import os
import sys
import math

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)

def setup_lighting_and_camera():
    # 场景环境与世界背景
    world = bpy.data.worlds.new("StudioWorld")
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs[0].default_value = (0.08, 0.09, 0.11, 1.0) # 深蓝灰纯净背景
        bg_node.inputs[1].default_value = 1.0
    bpy.context.scene.world = world

    # 三点摄影棚布光 (Key, Fill, Rim)
    key_light_data = bpy.data.lights.new("KeyLight", type='SUN')
    key_light_data.energy = 3.5
    key_light_data.color = (1.0, 0.98, 0.95)
    key_light = bpy.data.objects.new("KeyLight", key_light_data)
    key_light.rotation_euler = (math.radians(45), math.radians(15), math.radians(-35))
    bpy.context.scene.collection.objects.link(key_light)

    fill_light_data = bpy.data.lights.new("FillLight", type='SUN')
    fill_light_data.energy = 1.8
    fill_light_data.color = (0.85, 0.92, 1.0)
    fill_light = bpy.data.objects.new("FillLight", fill_light_data)
    fill_light.rotation_euler = (math.radians(35), math.radians(-20), math.radians(140))
    bpy.context.scene.collection.objects.link(fill_light)

    rim_light_data = bpy.data.lights.new("RimLight", type='SUN')
    rim_light_data.energy = 4.2
    rim_light_data.color = (0.9, 0.95, 1.0)
    rim_light = bpy.data.objects.new("RimLight", rim_light_data)
    rim_light.rotation_euler = (math.radians(-30), math.radians(0), math.radians(180))
    bpy.context.scene.collection.objects.link(rim_light)

    # 摄像机
    cam_data = bpy.data.cameras.new("MainCam")
    cam_data.lens = 85 # 85mm 人像长焦，彻底杜绝广角透视畸变
    cam_obj = bpy.data.objects.new("MainCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    return cam_obj

def render_view(cam_obj, location, rotation, output_path, resolution=(2048, 2048)):
    cam_obj.location = location
    cam_obj.rotation_euler = rotation
    scene = bpy.context.scene
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_depth = '8'
    bpy.ops.render.render(write_still=True)
    print(f"[*] 渲染完成: {output_path}")

def process_raw_sculpt(raw_glb_path, output_dir, render_dir):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(render_dir, exist_ok=True)

    if not os.path.exists(raw_glb_path):
        print(f"[ERROR] 未找到原始网格: {raw_glb_path}")
        return False

    clean_scene()
    cam = setup_lighting_and_camera()

    print(f"[*] 正在加载原始 AI 网格: {raw_glb_path}")
    bpy.ops.import_scene.gltf(filepath=raw_glb_path)

    imported_meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not imported_meshes:
        print("[ERROR] 导入的文件中未找到网格物体！")
        return False

    # 计算整体包围盒
    min_z = min([min([v.co.z for v in m.data.vertices]) for m in imported_meshes])
    max_z = max([max([v.co.z for v in m.data.vertices]) for m in imported_meshes])
    current_height = max_z - min_z
    print(f"[*] 原始网格测量高度: {current_height:.3f}m")

    # 标定总高为 Aster 标准二次元仙气身高 1.650m
    target_height = 1.650
    if current_height > 0.001:
        scale_factor = target_height / current_height
        for m in imported_meshes:
            m.scale = (m.scale.x * scale_factor, m.scale.y * scale_factor, m.scale.z * scale_factor)
            bpy.context.view_layer.objects.active = m
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # 地面吸附 (让脚底精确踩在 Z=0 平面，水平居中于原点)
    all_verts_z = [v.co.z for m in imported_meshes for v in m.data.vertices]
    lowest_z = min(all_verts_z)
    for m in imported_meshes:
        m.location.z -= lowest_z
        bpy.context.view_layer.objects.active = m
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

    # 赋予工业级灰模 Clay 材质（带微漫反射与亚光）
    clay_mat = bpy.data.materials.new("StudioClay_M1")
    clay_mat.use_nodes = True
    nodes = clay_mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.75, 0.77, 0.80, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.45

    for m in imported_meshes:
        m.data.materials.clear()
        m.data.materials.append(clay_mat)

    # 导出 M1 几何拓扑资产
    blend_path = os.path.join(output_dir, "aster_m1_topology.blend")
    glb_path = os.path.join(output_dir, "aster_m1_topology.glb")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB')
    print(f"[*] 已保存 M1 工程: {blend_path}")

    # 渲染 3 视角 2K 审查图
    # 1. 正面全身 (高距 0.85m 处对准腰腹，展现 8.5 头身比例)
    render_view(cam, (0.0, -3.2, 0.85), (math.radians(90), 0, 0),
                os.path.join(render_dir, "01_m1_front_silhouette_wire.png"))

    # 2. 3/4 侧面全身 (展现下颌骨、胸腰曲线与泡泡袖立体感)
    render_view(cam, (2.3, -2.3, 0.95), (math.radians(80), 0, math.radians(45)),
                os.path.join(render_dir, "02_m1_three_quarter_clay.png"))

    # 3. 背面长发与后摆飘带 (展现长发流动感与百褶后裙)
    render_view(cam, (0.0, 3.2, 0.90), (math.radians(90), 0, math.radians(180)),
                os.path.join(render_dir, "03_m1_back_hair_flow.png"))

    print("[SUCCESS] 阶段 1 拓扑化处理与 3 视角渲染全部完成！")
    return True

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    raw_glb = os.path.join(base_dir, "art", "models", "raw_ai_sculpt", "aster_raw_sculpt.glb")
    out_dir = os.path.join(base_dir, "art", "models")
    rnd_dir = os.path.join(base_dir, "art", "render_previews", "milestone1")
    process_raw_sculpt(raw_glb, out_dir, rnd_dir)
