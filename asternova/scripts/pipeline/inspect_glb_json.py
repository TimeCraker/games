"""Quick glTF JSON inspector: nodes, skins/bones, meshes, accessor min/max. Read-only."""
import json, struct, sys, os

def read_glb_json(path):
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:4] == b'glTF', 'not glb'
    length = struct.unpack('<I', data[8:12])[0]
    off = 20  # magic(4) ver(4) len(4) chunk0_len(4) chunk0_type(4) -> json starts at 20
    # proper walk
    off = 12
    j = None
    while off < length:
        clen, ctype = struct.unpack('<I4s', data[off:off+8])
        body = data[off+8:off+8+clen]
        if ctype == b'JSON':
            j = json.loads(body.decode('utf-8'))
        off += 8 + clen
        if ctype == b'JSON':
            break
    return j

def describe(path):
    j = read_glb_json(path)
    print('=' * 70)
    print('FILE:', os.path.basename(path))
    print('asset:', j.get('asset', {}).get('version'), '| generator:', j.get('asset', {}).get('generator', '?')[:90])
    nodes = j.get('nodes', [])
    meshes = j.get('meshes', [])
    print('nodes:', len(nodes), '| meshes:', len(meshes), '| skins:', len(j.get('skins', [])), '| images:', len(j.get('images', [])), '| materials:', len(j.get('materials', [])))
    skins = j.get('skins', [])
    for s in skins:
        names = [nodes[i].get('name', f'#{i}') for i in s.get('joints', [])]
        print('BONES(%d):' % len(names), ', '.join(names))
    for i, n in enumerate(nodes):
        tr = []
        if 'translation' in n: tr.append('T' + str([round(v, 4) for v in n['translation']]))
        if 'rotation' in n: tr.append('R' + str([round(v, 4) for v in n['rotation']]))
        if 'scale' in n: tr.append('S' + str([round(v, 4) for v in n['scale']]))
        if 'mesh' in n or 'skin' in n or not n.get('children'):
            print(f'  node[{i}] {n.get("name","?")} mesh={n.get("mesh")} skin={n.get("skin")} {" ".join(tr)}')
    for i, m in enumerate(meshes):
        prims = m.get('primitives', [])
        attrs = list(prims[0].get('attributes', {}).keys()) if prims else []
        print(f'  mesh[{i}] {m.get("name","?")} prims={len(prims)} attrs={attrs}')
    # position accessor bounds per mesh node
    accs = j.get('accessors', [])
    for n in nodes:
        if 'mesh' not in n:
            continue
        mesh = meshes[n['mesh']]
        for pi, p in enumerate(mesh.get('primitives', [])):
            ai = p.get('attributes', {}).get('POSITION')
            if ai is not None and 'min' in accs[ai] and 'max' in accs[ai]:
                mn, mx = accs[ai]['min'], accs[ai]['max']
                # node scale affects real size
                sc = n.get('scale', [1, 1, 1])
                size = [(mx[k] - mn[k]) * sc[k] for k in range(3)]
                print(f'  BBOX {n.get("name","?")}[prim{pi}] min={[round(v,4) for v in mn]} max={[round(v,4) for v in mx]} scaled_size={[round(v,4) for v in size]}')
    for i, img in enumerate(j.get('images', [])):
        print(f'  image[{i}]', img.get('name', img.get('uri', '?')))
    for i, mat in enumerate(j.get('materials', [])):
        pbr = mat.get('pbrMetallicRoughness', {})
        print(f'  mat[{i}]', mat.get('name', '?'), 'baseColorTexture=', pbr.get('baseColorTexture', {}).get('index'), 'metallic=', pbr.get('metallicFactor'), 'rough=', pbr.get('roughnessFactor'))

for p in sys.argv[1:]:
    try:
        describe(p)
    except Exception as e:
        print('ERR', p, repr(e))
