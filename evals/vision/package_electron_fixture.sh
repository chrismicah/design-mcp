#!/bin/bash
set -euo pipefail

if [ "$#" -ne 2 ] || [ "$(uname -s)" != Darwin ]; then
  echo "Usage on macOS: bash package_electron_fixture.sh ELECTRON_APP NEW_FIXTURE_APP" >&2
  exit 64
fi

runtime=$1
fixture=$2
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
bundle_id=org.designmcp.electronreviewfixture
plist=/usr/libexec/PlistBuddy
version=$("$plist" -c 'Print :CFBundleShortVersionString' "$runtime/Contents/Info.plist")
runtime_id=$("$plist" -c 'Print :CFBundleIdentifier' "$runtime/Contents/Info.plist")
if [ "$version" != 43.4.0 ] || [ "$runtime_id" != com.github.Electron ]; then
  echo "Expected the verified Electron 43.4.0 developer runtime." >&2
  exit 65
fi
if [ -e "$fixture" ] || [ -L "$fixture" ]; then
  echo "Choose a fresh app path for the owned fixture." >&2
  exit 73
fi

/usr/bin/ditto "$runtime" "$fixture"
contents="$fixture/Contents"
app="$contents/Resources/app"
mkdir -p "$app/evals/vision/fixtures" "$app/integrations/desktop"
cp "$repo/evals/vision/electron_smoke.mjs" "$app/evals/vision/"
cp "$repo/evals/vision/fixtures/electron-review.html" "$repo/evals/vision/fixtures/electron-review.js" \
  "$app/evals/vision/fixtures/"
cp "$repo/integrations/desktop/electron.mjs" "$app/integrations/desktop/"
cat > "$app/package.json" <<'JSON'
{"name":"design-mcp-electron-review-fixture","version":"1.0.0","main":"evals/vision/electron_smoke.mjs"}
JSON

"$plist" -c "Set :CFBundleIdentifier $bundle_id" "$contents/Info.plist"
"$plist" -c 'Set :CFBundleName Design MCP Electron Review Fixture' "$contents/Info.plist"
"$plist" -c 'Set :CFBundleDisplayName Design MCP Electron Review Fixture' "$contents/Info.plist"
for helper in "$contents/Frameworks/"*.app; do
  helper_info="$helper/Contents/Info.plist"
  helper_id=$("$plist" -c 'Print :CFBundleIdentifier' "$helper_info")
  "$plist" -c "Set :CFBundleIdentifier $bundle_id${helper_id#com.github.Electron}" "$helper_info"
done

# Seal the local development app from its nested code outward.
while IFS= read -r -d '' binary; do
  if [[ $(/usr/bin/file -b "$binary") == *Mach-O* ]]; then
    /usr/bin/codesign --force --sign - --timestamp=none "$binary"
  fi
done < <(/usr/bin/find "$contents/Frameworks" -type f \( -name '*.dylib' -o -perm -111 \) -print0)
while IFS= read -r -d '' bundle; do
  /usr/bin/codesign --force --sign - --timestamp=none "$bundle"
done < <(/usr/bin/find "$contents/Frameworks" -depth -type d \( -name '*.framework' -o -name '*.app' \) -print0)
/usr/bin/codesign --force --sign - --timestamp=none "$fixture"
/usr/bin/codesign --verify --deep --strict --verbose=2 -R="identifier \"$bundle_id\"" "$fixture"
