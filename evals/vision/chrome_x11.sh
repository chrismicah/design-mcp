#!/usr/bin/env bash
set -euo pipefail

proof="$4"
mkdir -p "$proof"
openbox --sm-disable >"$proof/window-manager.log" 2>&1 &
wm_pid=$!
trap 'kill "$wm_pid" 2>/dev/null || true' EXIT

for ((attempt=0; attempt<50; attempt++)); do
  if xprop -root _NET_SUPPORTING_WM_CHECK | grep -q 'window id # 0x[1-9a-fA-F]'; then
    node --experimental-websocket evals/vision/extension_smoke.mjs "$@"
    exit
  fi
  sleep 0.1
done

echo 'The X11 window manager did not become ready.' >&2
exit 1
