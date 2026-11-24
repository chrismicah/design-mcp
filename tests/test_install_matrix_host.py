import os
from pathlib import Path
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/verify_install_matrix.sh"


@pytest.mark.parametrize("system, os_version, machine, native_arm, rosetta, expected, outcome", [
    ("Darwin", "13.7.8", "arm64", "1", "0", "arm64", "PASS native host"),
    ("Darwin", "13.7.8", "x86_64", "", "", "x86_64", "PASS native host"),
    ("Darwin", "13.7.8", "x86_64", "1", "1", "x86_64", "Rosetta cannot certify"),
    ("Darwin", "13.7.8", "x86_64", "1", "", "x86_64", "Rosetta cannot certify"),
    ("Darwin", "15.8.2", "x86_64", "", "", "x86_64", "Observed macOS 15.8.2"),
    ("Darwin", "13.7.8", "arm64", "1", "0", "x86_64", "Observed macOS 13.7.8 on arm64"),
    ("Linux", "13.7.8", "x86_64", "", "", "x86_64", "requires a macOS host"),
])
def test_install_matrix_validates_os_and_native_cpu_before_install(
    tmp_path, system, os_version, machine, native_arm, rosetta, expected, outcome,
):
    binaries = {
        "uname": 'case "$1" in -s) echo "$TEST_SYSTEM";; -m) echo "$TEST_MACHINE";; *) exit 2;; esac',
        "sw_vers": 'test "$1" = -productVersion && echo "$TEST_VERSION"',
        "sysctl": 'case "$2" in hw.optional.arm64) v=$TEST_ARM;; sysctl.proc_translated) v=$TEST_ROSETTA;; *) exit 2;; esac\n'
                  'test -n "$v" && echo "$v"',
    }
    for name, source in binaries.items():
        path = tmp_path / name
        path.write_text(f"#!/bin/sh\n{source}\n")
        path.chmod(0o700)
    env = dict(os.environ, PATH=f"{tmp_path}:/usr/bin:/bin", TEST_SYSTEM=system, TEST_MACHINE=machine,
               TEST_VERSION=os_version, TEST_ARM=native_arm, TEST_ROSETTA=rosetta)
    if outcome.startswith("PASS"):
        command = ["--check-host", "13", expected]
    else:
        command = ["13", expected, "0" * 40, "/missing/uv", str(tmp_path / "install")]
    result = subprocess.run(["/bin/bash", SCRIPT, *command], env=env, capture_output=True, text=True)
    assert outcome in result.stdout + result.stderr
    assert result.returncode == (0 if outcome.startswith("PASS") else 2)
    assert not (tmp_path / "install").exists()
