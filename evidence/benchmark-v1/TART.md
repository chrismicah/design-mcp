# Fresh Mac verification

The hosted matrix covers both Mac CPU architectures on macOS 15. The shared clean-install script passed all eight hosted jobs. Use that script for each interpreter inside a fresh Tart guest. Record the image digest, guest `sw_vers`, `uname -m`, exact checkout SHA, both installer results, and the 17-tool smoke output. Tart runs on Apple Silicon. The Intel evidence comes from the hosted Intel runner. [Shared-script verification](https://github.com/chrismicah/design-mcp/actions/runs/44988412952) · [Tart documentation](https://tart.run/quick-start/)

The public Ventura base image resolved to `ghcr.io/cirruslabs/macos-ventura-base@sha256:9fb387bb987cdda942fbc27118296ed8e16a3359a672c95c6d5ac960165ef1c5` on November 21. The registry reported 22.6 GB compressed and a 50 GB logical disk. The image and guest version have yet to be booted or verified here. [Public image](https://github.com/orgs/cirruslabs/packages/container/package/macos-ventura-base)

Under the shared lease, clone the pinned image into a workspace-scoped `TART_HOME`. Mount a directory containing a `git archive` of the exact candidate read-only. Boot headless and check readiness with `tart exec`. Inside the guest, unpack the archive into a writable temporary directory.

```sh
run=$(mktemp -d)
tar -xf '/Volumes/My Shared Files/design-proof/candidate.tar' -C "$run"
uv python install 3.10 3.11 3.12 3.13
for version in 3.10 3.11 3.12 3.13; do
  py=$(uv python find --managed-python "$version")
  EXPECTED_ARCH=arm64 EXPECTED_PYTHON="$version" \
    bash "$run/scripts/verify_clean_install.sh" "$run" "$py" "$run/verification-$version"
done
```

Verify the guest reports macOS 13 before counting these results toward support on Ventura. Use the guest agent over `tart exec` on a compatible host. If the pinned guest cannot boot or exposes no guest agent, preserve the failure evidence and retry on compatible hardware or a prepared image.
