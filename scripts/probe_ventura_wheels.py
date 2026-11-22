"""Verify declared macOS 13 wheel availability without installing a package."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tomllib
from urllib.parse import quote
from urllib.request import urlopen

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import compatible_tags, cpython_tags, mac_platforms
from packaging.utils import canonicalize_name, parse_wheel_filename


ARCHES = {"aarch64": "arm64", "x86_64": "x86_64"}
MINORS = ("3.10", "3.11", "3.12", "3.13")
DEPLOYMENT_TARGET = (13, 0)
PYPI = "https://pypi.org"


def run(command, env=None):
    return subprocess.check_output(command, text=True, env=env, timeout=45)


def version_catalog(uv, minor):
    entries = json.loads(run([uv, "--no-config", "python", "list", "--only-downloads", "--all-platforms",
                              "--all-arches", "--output-format", "json", minor]))
    return {arch: next(entry for entry in entries if entry["arch"] == arch and entry["os"] == "macos"
                       and entry["implementation"] == "cpython" and entry["variant"] == "default")
            for arch in ARCHES}


def compile_inputs(uv, files, out, targets):
    env = {k: v for k, v in os.environ.items() if not k.startswith("UV_")}
    env.update(UV_CACHE_DIR=str(out / "uv-cache"), UV_CONCURRENT_DOWNLOADS="2",
               UV_HTTP_TIMEOUT="15", MACOSX_DEPLOYMENT_TARGET="13.0")
    results = {}
    for (arch, minor), interpreter in targets.items():
        requirements = {}
        for group, path in files.items():
            args = [uv, "--no-config", "--no-python-downloads", "pip", "compile",
                    "--only-binary", ":all:", "--default-index", PYPI + "/simple",
                    "--python-platform", f"{arch}-apple-darwin", "--python-version", interpreter["version"],
                    "--no-header", "--no-annotate", str(path)]
            body = run(args, env)
            (out / f"{arch}-{minor}-{group}.txt").write_text(body)
            parsed = [Requirement(line) for line in body.splitlines() if line.strip()]
            pins = {canonicalize_name(r.name): next(iter(r.specifier)).version for r in parsed
                    if len(r.specifier) == 1 and next(iter(r.specifier)).operator == "=="}
            if not pins or len(pins) != len(parsed):
                raise ValueError(f"Expected version pins for {arch} Python {minor} {group}")
            requirements[group] = pins
        results[arch, minor] = requirements
    return results


def release_metadata(pair):
    name, version = pair
    with urlopen(f"{PYPI}/pypi/{quote(name)}/{quote(version)}/json", timeout=15) as response:
        blob = response.read()
    data = json.loads(blob)
    if canonicalize_name(data["info"]["name"]) != name or data["info"]["version"] != version:
        raise ValueError(f"The index returned the wrong release for {name}=={version}")
    return pair, (data["urls"], sha256(blob).hexdigest())


def wheel_for(pair, metadata, version, ranks):
    files, metadata_digest = metadata
    options = []
    for file in files:
        filename = file["filename"]
        if not filename.endswith(".whl") or file["yanked"]:
            continue
        python = file.get("requires_python")
        if python and not SpecifierSet(python).contains(version):
            continue
        name, pin, _, tags = parse_wheel_filename(filename)
        if (name, str(pin)) != pair:
            raise ValueError(f"Unexpected wheel identity: {filename}")
        available = tags & ranks.keys()
        if available:
            tag = min(available, key=ranks.__getitem__)
            options.append((ranks[tag], filename, tag, file))
    if not options:
        return None
    _, filename, tag, file = min(options, key=lambda row: row[:2])
    return {"version": pair[1], "wheel": filename, "matched_tag": str(tag),
            "sha256": file["digests"]["sha256"], "metadata_sha256": metadata_digest}


def audit(uv, reference, out):
    pin = run(["git", "rev-parse", "--verify", reference + "^{commit}"]).strip()
    raw = run(["git", "show", pin + ":pyproject.toml"])
    project = tomllib.loads(raw)
    groups = {"runtime": project["project"]["dependencies"], "build_backend": project["build-system"]["requires"],
              "installers": ["pipx", "uv"]}
    files = {name: out / f"{name}.in" for name in groups}
    for name, path in files.items():
        path.write_text("".join(f"{entry}\n" for entry in groups[name]))
    targets = {(arch, minor): entry for minor in MINORS for arch, entry in version_catalog(uv, minor).items()}
    resolutions = compile_inputs(uv, files, out, targets)
    unique_pins = sorted({(name, pin) for groups in resolutions.values()
                          for pins in groups.values() for name, pin in pins.items()})
    with ThreadPoolExecutor(max_workers=3) as pool:
        metadata = dict(pool.map(release_metadata, unique_pins))

    matrix = []
    missed = []
    wheels = {}
    for (arch, minor), by_group in resolutions.items():
        interpreter = targets[arch, minor]
        version = interpreter["version"]
        python_version = tuple(map(int, minor.split(".")))
        platforms = list(mac_platforms(DEPLOYMENT_TARGET, ARCHES[arch]))
        tags = [*cpython_tags(python_version, platforms=platforms),
                *compatible_tags(python_version, interpreter=f"cp{minor.replace('.', '')}", platforms=platforms)]
        ranks = {tag: index for index, tag in enumerate(dict.fromkeys(tags))}
        reported = {}
        for group, pins in by_group.items():
            reported[group] = {}
            for name, pin in sorted(pins.items()):
                wheel = wheel_for((name, pin), metadata[name, pin], version, ranks)
                if wheel is None:
                    missed.append({"arch": ARCHES[arch], "python": version, "group": group, "pin": f"{name}=={pin}"})
                    reported[group][name] = None
                else:
                    filename = wheel["wheel"]
                    wheels[filename] = {k: wheel[k] for k in ("version", "sha256", "metadata_sha256")}
                    reported[group][name] = {"wheel": filename, "matched_tag": wheel["matched_tag"]}
        matrix.append({"architecture": ARCHES[arch], "python": version, "managed_interpreter_url": interpreter["url"],
                       "groups": reported})
    return {
        "scope": "Binary-only dependency resolution and an independent check of advertised PyPI wheel tags. "
                 "The managed interpreter URLs come from uv's catalog. There is no guest OS or installation in this check.",
        "source_commit": pin, "uv": run([uv, "--version"]).strip(), "macos_target": "13.0",
        "pyproject_sha256": sha256(raw.encode()).hexdigest(), "input_requirements": groups,
        "unique_release_metadata_reads": len(metadata), "wheels": wheels, "matrix": matrix, "missing_wheels": missed,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uv", default="uv")
    parser.add_argument("--ref", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True)
    result = audit(args.uv, args.ref, args.out.resolve())
    (args.out / "ventura-wheels.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Checked {len(result['matrix'])} targets and {result['unique_release_metadata_reads']} releases.")
    if result["missing_wheels"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
