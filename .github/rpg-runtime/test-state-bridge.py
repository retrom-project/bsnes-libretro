#!/usr/bin/env python3
"""Test the actual patched RetroArch state bridge with an async project-owned payload."""
from pathlib import Path
import subprocess
import sys

retroarch, output = map(Path, sys.argv[1:])
output.mkdir()
source = (retroarch / 'tasks/task_save.c').read_text()
start = source.index('extern void retrom_save_state_complete')
end = source.index('bool supports_states(void)', start)
harness = '''#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <malloc.h>
#include <emscripten.h>
#include "libco/libco.h"
static cothread_t primary, worker;
static void work(void) { for (;;) co_switch(primary); }
bool core_info_current_supports_savestate(void) { return true; }
size_t core_serialize_size(void) {
  if (!worker) { primary = co_active(); worker = co_create(16384, work); }
  co_switch(worker);
  return 4;
}
void *content_get_serialized_data(size_t *size) {
  unsigned char *result = malloc(*size);
  memcpy(result, "test", 4);
  return result;
}
int allocated(void) { return mallinfo().uordblks; }
'''
(output / 'state.c').write_text(harness + source[start:end])
subprocess.run(['emcc', str(output / 'state.c'), str(retroarch.parent / 'core/libco/libco.c'), '-I' + str(retroarch.parent / 'core'), '-O2', '--no-entry',
    '--js-library', str(retroarch / 'emscripten/emulatorjs.js'),
    '-sASYNCIFY=1', '-sASSERTIONS=1', '-sMODULARIZE=1', '-sENVIRONMENT=node',
    '-sWASM_ASYNC_COMPILATION=0',
    '-sEXPORTED_RUNTIME_METHODS=EmulatorJSGetState',
    '-sEXPORTED_FUNCTIONS=_save_state_info,_malloc,_free,_allocated',
    '-o', str(output / 'state.cjs')], check=True)
(output / 'run.cjs').write_text('''const assert = require('node:assert/strict');
const watchdog = setTimeout(() => { console.error('state bridge timed out'); process.exit(1); }, 10000);
Promise.resolve(require('./state.cjs')()).then(async (module) => {
  const expected = [116, 101, 115, 116];
  assert.deepEqual(Array.from(await module.EmulatorJSGetState()), expected);
  const allocated = module._allocated();
  for (let i = 0; i < 32; i++) {
    assert.deepEqual(Array.from(await module.EmulatorJSGetState()), expected);
  }
  assert.equal(module._allocated(), allocated, 'state bridge leaked native buffers');
  console.log('RetroArch async state bytes and ownership: PASS');
}).catch(error => {console.error(error); process.exitCode = 1;}).finally(() => clearTimeout(watchdog));
''')
subprocess.run(['node', str(output / 'run.cjs')], check=True)
