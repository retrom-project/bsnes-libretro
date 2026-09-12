#!/usr/bin/env python3
"""Exercise actual Asyncify fiber switching and recreation, without a game ROM."""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
(root / 'build').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='fiber-test.', dir=root / 'build') as output:
    subprocess.run([
        'docker', 'run', '--rm', '--platform', 'linux/amd64',
        '-v', f'{root}:/source:ro', '-v', f'{output}:/output',
        'emscripten/emsdk@sha256:90b757eb11fa9a0e3ce4d2d9f76d932a56018e4accc37b5a28b2783751e60eb7',
        'bash', '-c',
        f'trap "chown -R {os.getuid()}:{os.getgid()} /output" EXIT; '
        'emcc /source/.github/rpg-runtime/test-fiber.c /source/libco/libco.c '
        '-I/source -O2 -sASYNCIFY=1 -sASSERTIONS=1 -sEXIT_RUNTIME=1 '
        '-sWASM_ASYNC_COMPILATION=0 -o /output/test.cjs && node /output/test.cjs'
    ], check=True)
print('bsnes Asyncify fiber lifecycle: PASS')
