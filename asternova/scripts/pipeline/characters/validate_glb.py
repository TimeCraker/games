"""Validate deliverable skins, bind transforms, and animation payloads.

Structural checks complement the actual Blender/Godot screenshots. They do not
assert aesthetic quality or absence of clothing intersections.
"""
import argparse
import hashlib
import json
import pathlib
import struct
import sys

import numpy as np


def read_glb(path):
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    assert magic == 0x46546C67 and version == 2 and length == len(raw)
    json_length, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4E4F534A
    document = json.loads(raw[20:20+json_length])
    binary_start = 20+json_length
    binary_length, kind = struct.unpack_from('<II', raw, binary_start)
    assert kind == 0x004E4942
    return document, raw[binary_start+8:binary_start+8+binary_length]


def accessor(document, binary, index):
    entry = document['accessors'][index]
    view = document['bufferViews'][entry['bufferView']]
    dtype = {5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[entry['componentType']]
    width = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[entry['type']]
    size = np.dtype(dtype).itemsize
    start = view.get('byteOffset',0)+entry.get('byteOffset',0)
    values = np.ndarray((entry['count'],width), dtype=dtype, buffer=binary,
                        offset=start, strides=(view.get('byteStride',size*width),size)).copy()
    if entry.get('normalized') and entry['componentType'] != 5126:
        values = values.astype(float)/np.iinfo(dtype).max
    return values


def node_transform(node):
    if 'matrix' in node:
        return np.array(node['matrix']).reshape(4,4).T
    x,y,z,w = node.get('rotation',[0,0,0,1])
    matrix = np.eye(4)
    matrix[:3,:3] = [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
    matrix[:3,:3] *= np.array(node.get('scale',[1,1,1]))
    matrix[:3,3] = node.get('translation',[0,0,0])
    return matrix


def validate(path):
    doc, binary = read_glb(path)
    nodes = doc['nodes']
    parent = {child:i for i,n in enumerate(nodes) for child in n.get('children',[])}
    world = {}
    def transform(i):
        if i not in world:
            world[i] = (transform(parent[i]) if i in parent else np.eye(4)) @ node_transform(nodes[i])
        return world[i]
    report = {'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'meshes':[],'animations':[]}
    assert len(doc.get('skins',[])) >= 1, 'Missing skin'
    for index,node in enumerate(nodes):
        if 'mesh' not in node:
            continue
        assert 'skin' in node, f'Unskinned mesh: {node.get("name")}'
        skin = doc['skins'][node['skin']]
        matrices = accessor(doc,binary,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
        palette = np.array([np.linalg.inv(transform(index))@transform(joint)@inverse for joint,inverse in zip(skin['joints'],matrices)])
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            attrs = primitive['attributes']
            points = accessor(doc,binary,attrs['POSITION'])
            joints = accessor(doc,binary,attrs['JOINTS_0'])
            weights = accessor(doc,binary,attrs['WEIGHTS_0'])
            assert np.isfinite(points).all() and np.isfinite(weights).all()
            assert np.all(weights >= 0) and np.allclose(weights.sum(axis=1),1,atol=.001)
            assert joints.max() < len(skin['joints'])
            homogeneous = np.column_stack([points,np.ones(len(points))])
            transformed = np.zeros_like(homogeneous)
            for slot in range(4):
                transformed += np.einsum('nij,nj->ni',palette[joints[:,slot]],homogeneous)*weights[:,slot,None]
            error = float(np.max(np.linalg.norm(transformed[:,:3]-points,axis=1)))
            assert error < .0001, f'Broken bind transforms {error}'
            report['meshes'].append({'name':node.get('name'),'vertices':len(points),'max_bind_error_m':error,'max_weight_sum_error':float(abs(weights.sum(axis=1)-1).max())})
    for animation in doc.get('animations',[]):
        end = 0.0
        changing = 0
        for sampler in animation['samplers']:
            times = accessor(doc,binary,sampler['input']).ravel()
            values = accessor(doc,binary,sampler['output'])
            assert np.all(np.diff(times)>0) and np.isfinite(values).all()
            end = max(end,float(times[-1]))
            changing += int(np.max(np.ptp(values,axis=0))>.001)
        assert changing > 0, f'Static animation {animation.get("name")}'
        report['animations'].append({'name':animation.get('name'),'duration_s':end,'changing_tracks':changing})
    required = {'Idle','Walk','Run','Sprint','Jump','Fall','Land','Attack','Talk'}
    assert required.issubset({a['name'] for a in report['animations']})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory',type=pathlib.Path)
    parser.add_argument('--report',required=True,type=pathlib.Path)
    argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None
    args = parser.parse_args(argv)
    result = [validate(args.directory/f'{name}.glb') for name in ['white','orange','purple']]
    args.report.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Validated three GLBs: normalized skin weights, bind transforms and moving animation tracks.')
