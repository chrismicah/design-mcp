# Fresh Mac verification

The hosted matrix covers both Mac CPU architectures on macOS 15. The shared clean-install script passed all eight hosted jobs. Use that script for each interpreter inside a fresh Tart guest. Record the image digest, guest `sw_vers`, `uname -m`, exact checkout SHA, both installer results, and the 17-tool smoke output. Tart runs on Apple Silicon. The Intel evidence comes from the hosted Intel runner. [Shared-script verification](https://github.com/chrismicah/design-mcp/actions/runs/44988412952) · [Tart documentation](https://tart.run/quick-start/)

The public Ventura base image resolved to `ghcr.io/cirruslabs/macos-ventura-base@sha256:9fb387bb987cdda942fbc27118296ed8e16a3359a672c95c6d5ac960165ef1c5` on November 21. The registry reported 22.6 GB compressed and a 50 GB logical disk. The image and guest version have yet to be booted or verified here. [Public image](https://github.com/orgs/cirruslabs/packages/container/package/macos-ventura-base)

The Tart 2.42.0 pull stopped at 56% when available space reached 20.46 GiB. Memory pressure was normal. The workspace-local partial uses about 24 GiB. Preserve it and resume from the same state and image digest after the Data volume has sufficient space for the remaining image, guest writes, and the 20 GiB reserve. Tart reuses the partial disk and checks completed chunks against the image digests. The pull stopped before guest boot, so the install and MCP smoke checks remain open. [Tart disk pull implementation](https://github.com/cirruslabs/tart/blob/2.42.0/Sources/tart/OCI/Layerizer/DiskV2.swift)

The staged guest bundle contains `a29d405b40ed49383c1fc7b91ba0bc51cee5135f`, the revision verified by the eight-job direct Git matrix. The host preflight checked the archive and uv checksums and the commit embedded by Git. The archive SHA-256 is `8fdde74fbc67def5afe8624cc26c4d0aa99499e75e3f45e16dde862c5bdd8990`. The workspace-local boot script accepts the full revision and `--check-input` to verify the staged files before invoking Tart. The guest has yet to run. [Direct Git install matrix](https://github.com/chrismicah/design-mcp/actions/runs/45001580472)

Under the shared lease, clone the pinned image into a workspace-scoped `TART_HOME`, mount the checksummed bundle read-only and boot headless. Use `tart exec` to run the staged guest script. It verifies macOS 13 and arm64, then fetches the public Git revision without credentials. With the verified bootstrap uv on the guest path, the install loop is:

```sh
run=$(mktemp -d)
repo=https://github.com/chrismicah/design-mcp.git
rev=a29d405b40ed49383c1fc7b91ba0bc51cee5135f
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

Verify the guest reports macOS 13 before counting these results toward support on Ventura. Use the guest agent over `tart exec` on a compatible host. If the pinned guest cannot boot or exposes no guest agent, preserve the failure evidence and retry on compatible hardware or a prepared image.
