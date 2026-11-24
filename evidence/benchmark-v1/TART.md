# Fresh Mac verification

The earlier install pin `0978712` passed on **macOS 13.7.4 arm64** in a disposable copy of the existing Tart benchmark guest. Both installers fetched the exact commit on Python 3.10 through 3.13 with new installation directories. The transcript audit verified eight pinned installs, eight passing `doctor` calls and 48 stdio runs, including the opt-in URL refusal path. The clone was stopped and deleted. The scoped OCI cache remained empty. Intel Ventura runtime remains open. [Exact Ventura transcript audit](ventura-tart-0978712.json) · [Exact macOS 15 matrix](release-ci-0978712.json)

The earlier `a9e1211` pin passed the same eight installs and 48 stdio checks in a guest cloned from the freshly pulled image. The later `0978712` pin was verified with fresh installs on the existing OS image. [Earlier Ventura transcript audit](ventura-tart-a9e1211.json)

The binary-only check resolved `0978712` for all eight Ventura architecture and Python targets. PyPI metadata matched all 604 wheel selections, including the pin’s WebSocket dependency. All eight managed interpreter URLs returned HTTP 200 to HEAD. This checks dependency availability. Intel Ventura still needs the native runtime matrix below. [Exact-pin dependency receipt](ventura-wheel-pin-0978712.json)

An earlier fresh Tart guest verified eight installs and 24 stdio runs against `b868307`, using an earlier set of smoke commands. [First Ventura transcript audit](ventura-tart-b868307.json)

The prior install pin `f30e6ff` passed eight binary-only dependency resolutions at macOS 13 deployment targets. Independent PyPI metadata matched all **604 wheel selections** and all eight managed interpreter URLs returned HTTP 200 to HEAD. Tart input preflight verified the Git archive and runner hashes. The staged input is ready for a fresh arm64 guest when there is capacity. The host had 58.81 GiB free and held no owned Ventura VM. Current arm64 and Intel runtime checks remain open. [Exact dependency and staged input receipt](ventura-f30e6ff-preflight.json)

The current README pin `18b87522` has the same package and matrix verifier
inputs as `f30e6ff`. The host checked the current archive's embedded Git
SHA and all four staged files. The local Mac reported macOS 26.5.2 on
arm64, 23.83 GiB available, and an empty Tart VM directory. The native Intel
preflight refused the host, and a cold arm64 VM build did not fit the
30 GiB headroom floor. Both current-pin Ventura runtime cells still need
a qualified host. [Current archive and host receipt](ventura-18b87522-stage.json)

## Earlier attempts

The hosted matrix covers both Mac CPU architectures on macOS 15. The shared clean-install script passed all eight hosted jobs. Use that script for each interpreter inside a fresh Tart guest. Record the image digest, guest `sw_vers`, `uname -m`, exact checkout SHA, both installer results, and the 17-tool smoke output. Tart runs on Apple Silicon. The Intel evidence comes from the hosted Intel runner. [Shared-script verification](https://github.com/chrismicah/design-mcp/actions/runs/44988412952) · [Tart documentation](https://tart.run/quick-start/)

The current GitHub-hosted macOS images start at macOS 15. GitHub documents M1 hardware for the standard hosted arm64 runner. Tart 2.42.0 documents nested virtualization for Linux guests on M3 or M4 hosts running macOS 15 or later. Use an Apple Silicon Mac directly for the Ventura guest and a separate Ventura Intel Mac for the Intel runtime check. [Runner images](https://github.com/actions/runner-images#available-images) · [Runner hardware](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) · [Tart 2.42.0 virtualization requirements](https://github.com/openai/tart/blob/2.42.0/docs/faq.md#nested-virtualization-support)

The public Ventura base image resolved to `ghcr.io/cirruslabs/macos-ventura-base@sha256:9fb387bb987cdda942fbc27118296ed8e16a3359a672c95c6d5ac960165ef1c5` on November 21. A November 22 registry check read the pinned manifest's configuration, which declares `darwin` on `arm64`. The manifest records an upload on September 20, 2025 and a 50 GB logical disk. The registry reported 22.6 GB compressed. [Public image](https://github.com/orgs/cirruslabs/packages/container/package/macos-ventura-base)

The first Tart 2.42.0 pull stopped at 56% when available space reached 20.46 GiB. Memory pressure was normal. The partial disk held about 24 GiB. After available space recovered, Tart resumed the same image and checked the reused chunks against the image digests. [Tart disk pull implementation](https://github.com/cirruslabs/tart/blob/2.42.0/Sources/tart/OCI/Layerizer/DiskV2.swift)

The earlier guest bundle contained `2fcd31221671590152401d958b904141e438e453`, the revision verified by the eight-job direct Git matrix. The host preflight checked the archive and uv checksums and the commit embedded by Git. The archive SHA-256 is `0d12360b1b85927d0b14ccc35b364f8ace014f04f347751c1dac751993e72936`. The workspace-local boot script accepts the full revision and `--check-input` to verify the staged files before invoking Tart. [Direct Git install matrix](https://github.com/chrismicah/design-mcp/actions/runs/45010831792)

The host staged and checked the archive and uv bootstrap for `e1cd4eb82bc60269ce42223523f73a862c0086a5`. Git reported that exact commit in the archive, whose SHA-256 is `ade74d7f75b68d044e77e81a1f0f158be7da5883f0d928983c43a57a5f738e00`. The guest script fetches the public commit and checks the source provenance of both installs. [Bundle receipt](ventura-wheel-preflight.json)

The host also staged the earlier install pin `7bccfc14d4ce5652f81ee85f14bd56ee452a4aae`. Git verified the embedded commit and `shasum` verified the archive and uv binary. The pin uses the same `pyproject.toml` bytes as `e1cd4eb`. [Bundle hashes](browser-public-network-7bccfc1.json) · [macOS 15 installs](direct-git-install-7bccfc1.json)

On November 22, uv 0.13.9 resolved `e1cd4eb`'s runtime dependencies, build backend and installer requirements for **all eight macOS 13 targets**. PyPI metadata matched all **604 wheel selections** against Ventura tags and the specified managed Python versions. The eight interpreter download URLs returned HTTP 200 to HEAD requests. The corrected probe reports the Git commit that supplied `pyproject.toml`. Its matrix and wheel hashes match the earlier receipt, whose source field was overwritten by a dependency version. In that earlier run, the resolver rejected a macOS 14-only test wheel at the Ventura target on both architectures and accepted both at macOS 14. Repeat with Python 3.11 or later and `packaging` installed using `python3 scripts/probe_ventura_wheels.py --uv "$VENTURA_UV" --ref 7bccfc1 --out "$NEW_PROBE_DIR"`. [Wheel preflight receipt](ventura-wheel-preflight.json) · [uv target handling](https://github.com/astral-sh/uv/blob/0.13.9/crates/uv-configuration/src/target_triple.rs)

Under the shared lease, clone the pinned image into a workspace-scoped `TART_HOME`, mount the checksummed bundle read-only and boot headless. Use `tart exec` to run the staged guest script. The `7bccfc1` bundle now includes the same matrix verifier that runs on a native Intel Ventura Mac. The host and guest check the verifier and uv digests. The matrix checks the OS major version, native host architecture, and each interpreter's architecture. It fetches the exact public commit, exercises both installers with every Python minor, and saves separate logs for each version. [Matrix verifier](../../scripts/verify_install_matrix.sh)

The verifier passed all eight hosted macOS 15 cells with the staged script bytes. The run recorded 16 pinned installs and 32 stdio smoke runs. Each runner refused the Ventura preflight on its actual OS. The earlier serial Intel run completed Python 3.10 and 3.11 before the 16-minute limit. The succeeding CI run used independent interpreter cells. [Qualification receipt](native-install-matrix-qualification.json)

## Intel Ventura rerun

Use native uv on the Intel Ventura machine. The pinned x86_64 uv archive has SHA-256 digest `617a3211261b0fc739562f0071aa34e9739797c510208ede8e2977c30903d041`. Run the host preflight before installing. It rejected the reference Mac, which reported macOS 26.5.2 on arm64. [uv 0.13.9 assets](https://github.com/astral-sh/uv/releases/tag/0.13.9)

```sh
set -o pipefail
VENTURA_PIN=18b87522a49c545dd6204c20762d6fd64145d375
bash scripts/verify_install_matrix.sh --check-host 13 x86_64
bash scripts/verify_install_matrix.sh 13 x86_64 \
  "$VENTURA_PIN" "$(command -v uv)" "$NEW_EVIDENCE_DIRECTORY" \
  2>&1 | tee "$MATRIX_LOG"
```

Use the Tart launcher's `guest-install.log` on arm64 and the saved terminal log on Intel. Audit each full transcript with the expected architecture. The receipt records the SHA-256 of the original log and verifies both installer entry points and the exact tool names for each Python version. The audit accepted the archived complete arm64 run and both matrices assembled from hosted cells. It rejected the timed-out Intel run and eight altered transcripts. [Audit evidence](install-transcript-audit.json)

```sh
python3 scripts/audit_install_matrix.py 13 "$EXPECTED_ARCH" \
  "$VENTURA_PIN" "$MATRIX_LOG" --require-review > "$MATRIX_RECEIPT"
```

Verify the guest reports macOS 13 before counting these results toward support on Ventura. Tart 2.42.0 requires macOS 14 or later on the host for `tart exec` and a running guest agent. The base-image template available at the upload date installs the agent through launchd. Verify the agent connection at runtime. If the pinned guest cannot boot or exposes no guest agent, preserve the failure evidence and retry on compatible hardware or a prepared image. [Host requirement](https://github.com/openai/tart/blob/2.42.0/Sources/tart/Commands/Exec.swift) · [Guest template at upload](https://github.com/cirruslabs/macos-image-templates/blob/db71c44bc1aaf11ca0db08522f6fe3c0ff1440cc/templates/base.pkr.hcl#L155-L178)
