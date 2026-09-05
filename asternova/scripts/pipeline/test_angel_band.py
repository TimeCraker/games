import bpy, math, os

hair_mat = bpy.data.materials.get('Aster_Hair_Master_NPR')
if hair_mat:
    nodes = hair_mat.node_tree.nodes
    links = hair_mat.node_tree.links
    
    geom = nodes.new('ShaderNodeNewGeometry')
    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    links.new(geom.outputs['Position'], sep_xyz.inputs['Vector'])
    
    # Map range Z [1.46, 1.56] -> [0.0, 1.0]
    map_range = nodes.new('ShaderNodeMapRange')
    map_range.inputs['From Min'].default_value = 1.46
    map_range.inputs['From Max'].default_value = 1.56
    map_range.inputs['To Min'].default_value = 0.0
    map_range.inputs['To Max'].default_value = 1.0
    links.new(sep_xyz.outputs['Z'], map_range.inputs['Value'])
    
    halo_ramp = nodes.new('ShaderNodeValToRGB')
    halo_ramp.color_ramp.interpolation = 'CARDINAL'
    halo_ramp.color_ramp.elements[0].position = 0.20
    halo_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    
    el1 = halo_ramp.color_ramp.elements.new(0.42)
    el1.color = (0.50, 0.80, 1.0, 1.0)
    
    el2 = halo_ramp.color_ramp.elements.new(0.50)
    el2.color = (0.75, 0.95, 1.0, 1.0)
    
    el3 = halo_ramp.color_ramp.elements.new(0.58)
    el3.color = (0.50, 0.80, 1.0, 1.0)
    
    halo_ramp.color_ramp.elements[3].position = 0.80
    halo_ramp.color_ramp.elements[3].color = (0.0, 0.0, 0.0, 1.0)
    
    links.new(map_range.outputs['Result'], halo_ramp.inputs['Fac'])
    
    s2rgb = [n for n in nodes if n.type == 'SHADER_TO_RGB'][0]
    halo_mask = nodes.new('ShaderNodeMix')
    halo_mask.data_type = 'RGBA'
    halo_mask.blend_type = 'MULTIPLY'
    halo_mask.inputs['Factor'].default_value = 1.0
    links.new(halo_ramp.outputs['Color'], halo_mask.inputs[6])
    links.new(s2rgb.outputs['Color'], halo_mask.inputs[7])
    
    # Find mix_angel
    mix_nodes = [n for n in nodes if n.type == 'MIX' and n != halo_mask]
    if mix_nodes:
        links.new(halo_mask.outputs[2], mix_nodes[0].inputs[7])

out_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews'
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_angel_ring_band.png')
bpy.ops.render.render(write_still=True)
print("ANGEL RING BAND RENDERED")
