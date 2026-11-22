# Fresh Mac verification

The hosted matrix covers both Mac CPU architectures on macOS 15. The shared clean-install script passed all eight hosted jobs. Use that script for each interpreter inside a fresh Tart guest. Record the image digest, guest `sw_vers`, `uname -m`, exact checkout SHA, both installer results, and the 17-tool smoke output. Tart runs on Apple Silicon. The Intel evidence comes from the hosted Intel runner. [Shared-script verification](https://github.com/chrismicah/design-mcp/actions/runs/44988412952) · [Tart documentation](https://tart.run/quick-start/)

The current GitHub-hosted macOS images start at macOS 15. GitHub documents M1 hardware for the standard hosted arm64 runner. Tart 2.42.0 documents nested virtualization for Linux guests on M3 or M4 hosts running macOS 15 or later. Use an Apple Silicon Mac directly for the Ventura guest and a separate Ventura Intel Mac for the Intel runtime check. [Runner images](https://github.com/actions/runner-images#available-images) · [Runner hardware](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) · [Tart 2.42.0 virtualization requirements](https://github.com/openai/tart/blob/2.42.0/docs/faq.md#nested-virtualization-support)

The public Ventura base image resolved to `ghcr.io/cirruslabs/macos-ventura-base@sha256:9fb387bb987cdda942fbc27118296ed8e16a3359a672c95c6d5ac960165ef1c5` on November 21. A November 22 registry check read the pinned manifest's configuration, which declares `darwin` on `arm64`. The manifest records an upload on September 20, 2025 and a 50 GB logical disk. The registry reported 22.6 GB compressed. Boot and the guest-reported OS version are pending. [Public image](https://github.com/orgs/cirruslabs/packages/container/package/macos-ventura-base)

The Tart 2.42.0 pull stopped at 56% when available space reached 20.46 GiB. Memory pressure was normal. The workspace-local partial uses about 24 GiB. Preserve it and resume from the same state and image digest after the Data volume has sufficient space for the remaining image, guest writes, and the 20 GiB reserve. Tart reuses the partial disk and checks completed chunks against the image digests. The pull stopped before guest boot, so the install and MCP smoke checks remain open. [Tart disk pull implementation](https://github.com/cirruslabs/tart/blob/2.42.0/Sources/tart/OCI/Layerizer/DiskV2.swift)

The staged guest bundle contains `2fcd31221671590152401d958b904141e438e453`, the revision verified by the eight-job direct Git matrix. The host preflight checked the archive and uv checksums and the commit embedded by Git. The archive SHA-256 is `0d12360b1b85927d0b14ccc35b364f8ace014f04f347751c1dac751993e72936`. The workspace-local boot script accepts the full revision and `--check-input` to verify the staged files before invoking Tart. The guest has yet to run. [Direct Git install matrix](https://github.com/chrismicah/design-mcp/actions/runs/45010831792)

The host also staged and checked the archive and uv bootstrap for `f17bd6f79fff62d1ec3e051b29d930ccb32b3a46`, the candidate with profile-local Chrome review history. The archive embeds that exact commit and has SHA-256 `12d6f713c1ede2393be57d49d649173b285b179edb7b52cbbf0457d3a4a0bf00`. The partial Ventura image is ready to resume with this bundle when disk headroom permits. [Candidate changes](https://github.com/chrismicah/design-mcp/commit/f17bd6f79fff62d1ec3e051b29d930ccb32b3a46) · [macOS 15 candidate runs](https://github.com/chrismicah/design-mcp/actions/runs/45026602037)

On November 22, the staged uv 0.13.9 resolved the pinned source's runtime dependencies, build backend and installer requirements for **all eight macOS 13 targets**. PyPI metadata independently matched all **604 wheel selections** against Ventura tags and the exact managed Python versions. The eight interpreter download URLs returned HTTP 200 to HEAD requests. On both architectures, the resolver rejected a macOS 14-only test wheel at the Ventura target and accepted it at macOS 14. Repeat with Python 3.11 or later and `packaging` installed, using `python3 scripts/probe_ventura_wheels.py --uv "$VENTURA_UV" --ref 2fcd312 --out "$NEW_PROBE_DIR"`. The guest install and server startup still require runtime verification. [Wheel preflight receipt](ventura-wheel-preflight.json) · [uv target handling](https://github.com/astral-sh/uv/blob/0.13.9/crates/uv-configuration/src/target_triple.rs)

Under the shared lease, clone the pinned image into a workspace-scoped `TART_HOME`, mount the checksummed bundle read-only and boot headless. Use `tart exec` to run the staged guest script. It verifies macOS 13 and arm64, then fetches the public Git revision without credentials. With the verified bootstrap uv on the guest path, the install loop is:

```sh
run=$(mktemp -d)
repo=https://github.com/chrismicah/design-mcp.git
rev=f17bd6f79fff62d1ec3e051b29d930ccb32b3a46
export GIT_TERMINAL_PROMPT=0
git init -q "$run/source"
git -C "$run/source" fetch --no-tags --depth=1 "$repo" "$rev"
git -C "$run/source" checkout --detach FETCH_HEAD
test "$(git -C "$run/source" rev-parse HEAD)" = "$rev"
uv python install 3.10 3.11 3.12 3.13
for version in 3.10 3.11 3.12 3.13; do
  py=$(uv python find --managed-python "$version")
  EXPECTED_ARCH=arm64 EXPECTED_PYTHON="$version" \
    bash "$run/source/scripts/verify_clean_install.sh" "$run/source" "$py" "$run/verification-$version" "$repo"
done
```

Verify the guest reports macOS 13 before counting these results toward support on Ventura. Tart 2.42.0 requires macOS 14 or later on the host for `tart exec` and a running guest agent. The base-image template available at the upload date installs the agent through launchd. Verify the agent connection at runtime. If the pinned guest cannot boot or exposes no guest agent, preserve the failure evidence and retry on compatible hardware or a prepared image. [Host requirement](https://github.com/openai/tart/blob/2.42.0/Sources/tart/Commands/Exec.swift) · [Guest template at upload](https://github.com/cirruslabs/macos-image-templates/blob/db71c44bc1aaf11ca0db08522f6fe3c0ff1440cc/templates/base.pkr.hcl#L155-L178)
