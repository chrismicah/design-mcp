#!/bin/bash
set -euo pipefail

if [[ $# != 3 && $# != 4 ]]; then
  printf 'Usage: %s SOURCE_CHECKOUT PYTHON_EXECUTABLE NEW_SCRATCH_DIRECTORY [GIT_URL]\n' "$0" >&2
  exit 2
fi

checkout=$(cd "$1" && pwd -P)
python=$2
mkdir "$3"
scratch=$(cd "$3" && pwd -P)
install_source=$checkout
if [[ $# == 4 ]]; then
  revision=$(git -C "$checkout" rev-parse HEAD)
  install_source="git+$4@$revision"
fi

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
"$installer/python" -m pip install pipx uv
"$installer/pipx" install --python "$python" "$install_source"
"$installer/uv" tool install --no-python-downloads --python "$python" "$install_source"

pipx_python="$PIPX_HOME/venvs/design-mcp/bin/python"
uv_python="$UV_TOOL_DIR/design-mcp/bin/python"
if [[ $# == 4 ]]; then
  for installed_python in "$pipx_python" "$uv_python"; do
    "$installed_python" -I - "$revision" <<'PY'
from importlib.metadata import distribution
import json
import sys

package = distribution("design-mcp")
provenance = json.loads(package.read_text("direct_url.json"))
vcs = provenance["vcs_info"]
if vcs["vcs"] != "git" or vcs["commit_id"] != sys.argv[1]:
    raise SystemExit(f"The install did not resolve the requested Git commit: {vcs}")
print(f"PASS pinned Git install — {vcs['commit_id']}")
files = {path.as_posix() for path in package.files}
for obsolete in ("patterns.json", "vision_results.json", "batch_list.json", "remaining_vision.json"):
    if f"design_mcp/data/{obsolete}" in files:
        raise SystemExit(f"The distribution still contains {obsolete}")
if any(path.startswith("design_mcp/prompts/") for path in files):
    raise SystemExit("The distribution still contains the archived prompt templates")
print("PASS package boundary — excludes legacy corpus, offline queues and archived prompts")
PY
  done
fi

verify_installed_tool() {
  local executable=$1 client_python=$2 report extension
  "$executable" version
  report=$(unset DESIGN_MCP_SURFACE && "$executable" doctor)
  printf '%s\n' "$report"
  grep -F "PASS interpreter — $python_minor." <<< "$report"
  grep -F 'PASS stdio tools/list — v2, 3 tools' <<< "$report"
  (unset DESIGN_MCP_SURFACE && "$client_python" -I "$checkout/scripts/smoke_design_mcp.py" "$executable" serve)
  DESIGN_MCP_SURFACE=both "$client_python" -I "$checkout/scripts/smoke_design_mcp.py" "$executable" serve
  DESIGN_MCP_SURFACE=legacy "$client_python" -I "$checkout/scripts/smoke_design_mcp.py" "$executable" serve
  (unset DESIGN_MCP_SURFACE && "$client_python" -I "$checkout/scripts/smoke_design_mcp.py" "$executable" serve --review)
  DESIGN_MCP_SURFACE=both "$client_python" -I "$checkout/scripts/smoke_design_mcp.py" "$executable" serve --review
  DESIGN_MCP_SURFACE=legacy "$client_python" -I "$checkout/scripts/smoke_design_mcp.py" "$executable" serve --review
  extension=$("$executable" review --extension-path | head -1)
  test -f "$extension/manifest.json"
  test -f "$extension/popup.html"
  "$executable" review-app --help >/dev/null
}

cd "$scratch"
verify_installed_tool "$PIPX_BIN_DIR/design-mcp" "$pipx_python"
verify_installed_tool "$UV_TOOL_BIN_DIR/design-mcp" "$uv_python"
