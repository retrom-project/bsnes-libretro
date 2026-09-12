# Retrom bsnes fork

Keep `master` as the upstream mirror. Develop on `feat/*`, `fix/*` or `build/*`
from the maintenance branch in `retrom-fork.json`. Core code and build recipes
belong here; never add Retrom host APIs or private game/firmware fixtures.

Build candidates through `.github/rpg-runtime/build-candidate.sh` and Retrom's
explicit `pfb-core-build`. Preserve the pinned Emscripten and RetroArch inputs,
source digest validation and upstream licenses. Validate real gameplay and
cross-Launch state restoration in the PFB before proposing publication.
