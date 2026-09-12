#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
output=${1:?absolute empty output directory is required}
python3 "$root/.github/rpg-runtime/candidate_descriptor.py" prepare "$output"
mkdir -p "$root/build" "$root/.cache"
linker="$root/.cache/retroarch-5a21e08.tar.gz"
if [[ ! -f "$linker" ]]; then
  curl --fail --location --retry 3 --retry-all-errors \
    https://codeload.github.com/EmulatorJS/RetroArch/tar.gz/5a21e08a5de7649cfa6416d6843c0c40de27714e \
    -o "$linker.download"
  mv "$linker.download" "$linker"
fi
test "$(sha256sum "$linker" | cut -d' ' -f1)" = 98147121cac2c4720d8d3998e0076d0c6e62977240b0a5d50b413a5666803c10
work=$(mktemp -d "$root/build/retrom-bsnes-web.XXXXXX")
trap 'rm -rf "$work"' EXIT INT TERM
mkdir -p "$work/raw" "$work/build"
python3 "$root/.github/rpg-runtime/test-fiber-contract.py"
source_digest=$(python3 "$root/.github/rpg-runtime/candidate_descriptor.py" digest "$output")
python3 "$root/.github/rpg-runtime/candidate_descriptor.py" paths "$output" > "$work/source-files"
tar --mtime=@0 --owner=0 --group=0 --numeric-owner -C "$root" --null --verbatim-files-from -T "$work/source-files" -cf "$work/source.tar"

export RETROM_HOST_UID="$(id -u)"
export RETROM_HOST_GID="$(id -g)"
if ! docker run --rm --platform linux/amd64 --hostname retrom-bsnes \
  --env RETROM_HOST_UID --env RETROM_HOST_GID \
  --volume "$work/source.tar:/source.tar:ro" \
  --volume "$linker:/retroarch.tar.gz:ro" \
  --volume "$root/.github/rpg-runtime:/recipe:ro" \
  --volume "$work/build:/work" \
  --volume "$work/raw:/output" \
  emscripten/emsdk@sha256:90b757eb11fa9a0e3ce4d2d9f76d932a56018e4accc37b5a28b2783751e60eb7 \
  /recipe/build-emulatorjs-core.sh bsnes \
  >"$work/build.log" 2>&1; then
  tail -200 "$work/build.log" >&2
  exit 1
fi

test "$source_digest" = "$(python3 "$root/.github/rpg-runtime/candidate_descriptor.py" digest "$output")"
stage="$work/stage"
mkdir -p "$stage"
install -m 0644 "$work/raw/bsnes_libretro.js" "$stage/"
install -m 0644 "$work/raw/bsnes_libretro.wasm" "$stage/"
install -m 0644 "$root/LICENSE.txt" "$stage/license.txt"
printf '%s\n' '{"minimumEJSVersion":"4.3.0","version":"2.0.3"}' > "$stage/build.json"
printf '%s\n' '{"name":"bsnes","extensions":["sfc","smc","swc","fig"],"makeoptions":{"buildpath":"./","makescript":"Makefile","arguments":[]},"options":{},"save":"SRM","license":"LICENSE.txt","repo":"https://github.com/retrom-project/bsnes-libretro"}' > "$stage/core.json"

(cd "$stage" && 7z a -mtm=off -mta=off -mtc=off -bd -bso0 -bsp0 -t7z "$output/bsnes-wasm.data" \
  bsnes_libretro.js bsnes_libretro.wasm build.json core.json license.txt)
install -m 0644 "$root/LICENSE.txt" "$output/LICENSE.txt"

gzip -n -c "$work/source.tar" > "$output/source.tar.gz"
