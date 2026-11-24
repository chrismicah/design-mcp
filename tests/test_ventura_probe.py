from scripts import probe_ventura_wheels as probe


def test_wheel_audit_retains_the_source_commit(monkeypatch, tmp_path):
    commit = "a" * 40
    python = "3.12.10"
    release = "2.4.0"
    project = '[project]\ndependencies = ["example"]\n[build-system]\nrequires = ["example"]\n'

    def run(command):
        if command[:3] == ["git", "rev-parse", "--verify"]:
            return commit
        if command == ["git", "show", f"{commit}:pyproject.toml"]:
            return project
        assert command == ["uv", "--version"]
        return "uv 0.13.9"

    monkeypatch.setattr(probe, "run", run)
    monkeypatch.setattr(probe, "MINORS", ("3.12",))
    monkeypatch.setattr(probe, "version_catalog", lambda *_: {
        "aarch64": {"version": python, "url": "https://example.com/cpython.tgz"},
    })
    monkeypatch.setattr(probe, "compile_inputs", lambda *_: {
        ("aarch64", "3.12"): {"runtime": {"example": release}},
    })
    monkeypatch.setattr(probe, "release_metadata", lambda pair: (pair, ([{
        "filename": f"example-{release}-py3-none-any.whl",
        "yanked": False,
        "digests": {"sha256": "b" * 64},
    }], "c" * 64)))

    result = probe.audit("uv", "candidate", tmp_path)
    assert result["source_commit"] == commit
    assert result["wheels"][f"example-{release}-py3-none-any.whl"]["version"] == release
