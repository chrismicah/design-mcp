#!/bin/bash
set -euo pipefail

usage() {
  printf 'Usage: %s [--check-host] MACOS_MAJOR ARCH [COMMIT UV_EXECUTABLE NEW_EVIDENCE_DIRECTORY]\n' "$0" >&2
  exit 2
}

check_only=false
if [[ ${1:-} == --check-host ]]; then
  check_only=true
  shift
  [[ $# == 2 ]] || usage
else
  [[ $# == 5 ]] || usage
fi

major=$1
expected_arch=$2
[[ $major =~ ^[1-9][0-9]*$ ]] || usage
[[ $expected_arch == arm64 || $expected_arch == x86_64 ]] || usage

if [[ $(uname -s) != Darwin ]]; then
  printf 'The install matrix requires a macOS host.\n' >&2
  exit 2
fi
os_version=$(sw_vers -productVersion)
arch=$(uname -m)
arm_capability=$(sysctl -n hw.optional.arm64 2>/dev/null || true)
translated=$(sysctl -n sysctl.proc_translated 2>/dev/null || true)
if [[ $os_version != "$major".* || $arch != "$expected_arch" ]]; then
  printf 'Expected macOS %s on %s. Observed macOS %s on %s.\n' "$major" "$expected_arch" "$os_version" "$arch" >&2
  exit 2
fi
if [[ $translated == 1 || ( $expected_arch == x86_64 && $arm_capability == 1 ) ]]; then
  printf 'Use a native shell on the requested architecture. Rosetta cannot certify an Intel install.\n' >&2
  exit 2
fi
if [[ $check_only == true ]]; then
  printf 'PASS native host — macOS %s %s\n' "$os_version" "$arch"
  exit
fi

revision=$3
[[ $revision =~ ^[0-9a-f]{40}$ ]] || usage
uv="$(cd "$(dirname "$4")" && pwd -P)/$(basename "$4")"
[[ -x $uv ]] || usage
mkdir "$5"
output=$(cd "$5" && pwd -P)

repo='https://github.com/chrismicah/design-mcp.git'
export GIT_TERMINAL_PROMPT=0 GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
export UV_PYTHON_INSTALL_DIR="$output/python" UV_CACHE_DIR="$output/bootstrap-cache"
export UV_NO_MODIFY_PATH=1

{
  sw_vers
  printf 'Architecture: %s\nRosetta: %s\nSource commit: %s\n' "$arch" "${translated:-0}" "$revision"
  "$uv" --version
} | tee "$output/host.txt"
git init -q "$output/source"
git -C "$output/source" fetch --no-tags --depth=1 "$repo" "$revision"
git -C "$output/source" checkout --detach FETCH_HEAD
[[ $(git -C "$output/source" rev-parse HEAD) == "$revision" ]]

for version in 3.10 3.11 3.12 3.13; do
  {
    "$uv" --no-config python install "$version"
    interpreter=$("$uv" --no-config python find --managed-python "$version")
    actual=$("$interpreter" -I -c 'import platform; print(platform.machine())')
    if [[ $actual != "$arch" ]]; then
      printf 'Python %s runs as %s. Expected %s.\n' "$version" "$actual" "$arch" >&2
      exit 2
    fi
    EXPECTED_ARCH=$arch EXPECTED_PYTHON=$version bash "$output/source/scripts/verify_clean_install.sh" \
      "$output/source" "$interpreter" "$output/install-$version" "$repo"
  } 2>&1 | tee "$output/python-$version.log"
done
printf 'PASS both installers and stdio smoke on macOS %s %s, Python 3.10–3.13, source %s\n' \
  "$os_version" "$arch" "$revision" | tee "$output/verified.txt"
