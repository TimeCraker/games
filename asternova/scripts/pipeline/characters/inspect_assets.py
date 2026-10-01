"""Record immutable input identities and actual GLB contents."""
import argparse
import hashlib
import json
import pathlib
import struct
import sys


def inspect(root):
    config = json.loads(pathlib.Path(__file__).with_name('characters.json').read_text(encoding='utf-8'))
    rows = []
    for name, spec in config['characters'].items():
        for role in ['body', 'outfit', 'hair']:
            path = root/spec['directory']/'3D模型'/spec[role]
            data = path.read_bytes()
            assert data[:4] == b'glTF'
            size, kind = struct.unpack_from('<II', data, 12)
            assert kind == 0x4e4f534a
            doc = json.loads(data[20:20+size])
            primitives = [p for m in doc['meshes'] for p in m['primitives']]
            rows.append({'character': name, 'role': role, 'path': str(path),
                         'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
                         'meshes': len(doc['meshes']), 'skins': len(doc.get('skins', [])),
                         'animations': len(doc.get('animations', [])),
                         'primitive_modes': [p.get('mode', 4) for p in primitives]})
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=pathlib.Path, required=True)
    parser.add_argument('--report', type=pathlib.Path, required=True)
    argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None
    args = parser.parse_args(argv)
    args.report.write_text(json.dumps(inspect(args.source_root), ensure_ascii=False, indent=2), encoding='utf-8')
    print('Recorded nine source GLBs, their roles, hashes and actual skin/animation counts.')
