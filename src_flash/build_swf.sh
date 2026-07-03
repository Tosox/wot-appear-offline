#!/usr/bin/env bash
# Builds appear_offline_contacts_hook.swf from our AS3 sources using mxmlc.
#
# Approach: compile against minimal *external* signature stubs (src_flash/stubs)
# so the game's real net.wg classes are used at runtime and are NOT embedded.
# The output is a bare Scaleform view SWF (document class = AppearOfflineHookUI,
# the alias the Python side registers), forced to SWF version 17 to match the
# game's own SWFs (GFx rejects newer versions).
#
# Artifacts (the .swc and the .swf) are written to ../build/, never next to the
# sources. Requires: Apache Flex SDK + playerglobal (see repo README /
# .work/tools/flex).
set -euo pipefail
cd "$(dirname "$0")"

BUILD="../build"
mkdir -p "$BUILD"
BUILD="$(cd "$BUILD" && pwd)"

# Absolute path required: the SDK resolves {playerglobalHome} against its own
# config dir, not the CWD, so a relative path fails.
FLEX="$(cd "${FLEX_HOME:-../.work/tools/flex}" && pwd)"
export PLAYERGLOBAL_HOME="$FLEX/frameworks/libs/player"

SWF="$BUILD/appear_offline_contacts_hook.swf"

echo "[1/2] compc: external stub swc"
"$FLEX/bin/compc" -source-path stubs -include-sources stubs \
  -target-player=11.1 -output "$BUILD/wgstub.swc" >/dev/null

echo "[2/2] mxmlc: hook swf"
"$FLEX/bin/mxmlc" src/AppearOfflineHookUI.as \
  -source-path=src \
  -external-library-path+="$BUILD/wgstub.swc" \
  -static-link-runtime-shared-libraries=true \
  -target-player=11.1 -swf-version=17 \
  -output "$SWF" >/dev/null

printf 'built %s (v%d, %d bytes)\n' "$SWF" \
  "$(od -An -j3 -N1 -tu1 "$SWF" | tr -d ' ')" \
  "$(wc -c < "$SWF")"
