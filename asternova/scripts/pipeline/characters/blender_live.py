"""Bridge to the installed Blender MCP addon's localhost JSON protocol.

This is a socket client, not a registered Codex MCP server. Blender remains
visible and serves all bpy operations on its main thread. No cloud services.
"""
import argparse
import json
from pathlib import Path
import socket


def request(command, params, timeout=180):
    with socket.create_connection(('127.0.0.1', 9876), timeout=10) as connection:
        connection.settimeout(timeout)
        connection.sendall(json.dumps({'type': command, 'params': params}).encode())
        received = bytearray()
        while True:
            chunk = connection.recv(65536)
            if not chunk:
                raise RuntimeError('Blender disconnected before completing the response')
            received.extend(chunk)
            try:
                result = json.loads(received.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                continue
            if result.get('status') != 'success':
                raise RuntimeError(result)
            return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--code-file', type=Path)
    parser.add_argument('--screenshot', type=Path)
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    if args.code_file:
        result = request('execute_code', {'code': args.code_file.read_text(encoding='utf-8')}, args.timeout)
    elif args.screenshot:
        result = request('get_viewport_screenshot', {'filepath': str(args.screenshot.resolve()), 'max_size': 1600})
    else:
        result = request('get_scene_info', {})
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
