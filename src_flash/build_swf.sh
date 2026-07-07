#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

BUILD="../build"
mkdir -p "$BUILD"
BUILD="$(cd "$BUILD" && pwd)"

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
