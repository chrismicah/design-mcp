#!/bin/bash
set -euo pipefail

if [[ $# != 3 ]]; then
  printf 'Usage: %s SOURCE_CHECKOUT PYTHON_EXECUTABLE NEW_SCRATCH_DIRECTORY\n' "$0" >&2
  exit 2
fi

checkout=$(cd "$1" && pwd -P)
python=$2
mkdir "$3"
scratch=$(cd "$3" && pwd -P)

architecture=$(uname -m)
python_minor=$("$python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ ${EXPECTED_ARCH:-$architecture} != "$architecture" || ${EXPECTED_PYTHON:-$python_minor} != "$python_minor" ]]; then
  printf 'Unexpected test host or Python: %s, %s\n' "$architecture" "$python_minor" >&2
  exit 2
fi
printf 'Host: %s macOS %s, %s\n' "$architecture" "$(sw_vers -productVersion)" "$("$python" -V)"

export PIPX_HOME="$scratch/pipx-home"
export PIPX_BIN_DIR="$scratch/pipx-bin"
export PIPX_MAN_DIR="$scratch/pipx-man"
export PIP_CACHE_DIR="$scratch/pip-cache"
export UV_TOOL_DIR="$scratch/uv-tools"
export UV_TOOL_BIN_DIR="$scratch/uv-bin"
export UV_CACHE_DIR="$scratch/uv-cache"
export UV_NO_MODIFY_PATH=1

"$python" -m venv "$scratch/installer"
installer="$scratch/installer/bin"
"$installer/python" -m pip install pipx uv "fastmcp==4.1.8; python_version < '3.11'" "fastmcp~=4.2.4; python_version >= '3.11'"
"$installer/pipx" install --python "$python" "$checkout"
"$installer/uv" tool install --no-python-downloads --python "$python" "$checkout"

cd "$scratch"
for executable in "$PIPX_BIN_DIR/design-mcp" "$UV_TOOL_BIN_DIR/design-mcp"; do
  "$executable" version
  report=$(unset DESIGN_MCP_SURFACE && "$executable" doctor)
  printf '%s\n' "$report"
  grep -F "PASS interpreter — $python_minor." <<< "$report"
  grep -F 'PASS stdio tools/list — v2, 3 tools' <<< "$report"
  (unset DESIGN_MCP_SURFACE && "$installer/python" "$checkout/scripts/smoke_design_mcp.py" "$executable" serve)
  DESIGN_MCP_SURFACE=both "$installer/python" "$checkout/scripts/smoke_design_mcp.py" "$executable" serve
  extension=$("$executable" review --extension-path | head -1)
  test -f "$extension/manifest.json"
  test -f "$extension/popup.html"
  "$executable" review-app --help >/dev/null
done
