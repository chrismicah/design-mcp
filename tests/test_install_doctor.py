import asyncio
import hashlib
from importlib import metadata
import json
from pathlib import Path
import runpy
import sys
from threading import Event
import zipfile

import pytest
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

from design_mcp import cli, corpus, doctor, resources
from design_mcp.direction_records import library
from design_mcp.directions import check, direct, react


ROOT = Path(__file__).resolve().parents[1]


def project_metadata():
    try:
        import tomllib
    except ImportError:  # Python 3.10, provided by pytest
        import tomli as tomllib
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


@pytest.mark.parametrize(("python", "version"), [
    ("3.10", "4.1.8"), ("3.11", "4.2.4"), ("3.12", "4.2.4"), ("3.13", "4.2.4"),
])
def test_interpreter_selects_one_supported_fastmcp(python, version):
    project = project_metadata()["project"]
    assert python in SpecifierSet(project["requires-python"])
    assert "3.9" not in SpecifierSet(project["requires-python"])
    requirements = [Requirement(entry) for entry in project["dependencies"]]
    matching = [req for req in requirements if req.name == "fastmcp"
                and req.marker.evaluate({"python_version": python})]
    assert len(matching) == 1 and version in matching[0].specifier
    if python == "3.10":
        assert "4.2.4" not in matching[0].specifier
    assert project["scripts"] == {"design-mcp": "design_mcp.cli:main"}


def test_distribution_data_selection_and_canonical_source_bytes():
    config = project_metadata()["tool"]["setuptools"]
    selected = {path.relative_to(ROOT / "design_mcp").as_posix()
                for pattern in config["package-data"]["design_mcp"]
                for path in (ROOT / "design_mcp").glob(pattern)}
    selected.difference_update(config["exclude-package-data"]["design_mcp"])
    assert not (selected & {"data/patterns.json", "data/batch_list.json", "data/remaining_vision.json",
                            "data/vision_results.json"})
    assert {"data/directions.json", "data/tokens/token_sets.json", "prompts/analyze_screen.md"} <= selected
    assert corpus.read_bundled() == (ROOT / "data" / "patterns.json").read_bytes()


@pytest.mark.asyncio
async def test_archive_resources_keep_directions_offline(tmp_path, monkeypatch):
    name = "tokens/semantic_tokens.json"
    with zipfile.ZipFile(tmp_path / "resources.zip", "w") as archive:
        for member in ("directions.json", name):
            archive.writestr("data/" + member, resources.data_file(member).read_bytes())
        monkeypatch.setattr(resources, "files", lambda package: zipfile.Path(archive))
        monkeypatch.setattr(corpus, "_download", lambda: pytest.fail("Unexpected download"))
        library.cache_clear()
        try:
            assert corpus.read_bundled() is None
            assert resources.read_json(name)["light"]
            result = await direct("Stage manager turnaround board")
            assert result["direction"]["id"] == "stage-call-sheet"
            assert (await react("stage-call-sheet", "calmer"))["changes"]
            assert "findings" in await check("<main>Studio B</main>")
        finally:
            library.cache_clear()


@pytest.mark.asyncio
async def test_default_server_lists_tools_and_serves_directions_during_a_cold_lookup(monkeypatch,
                                                                                     curated_pattern_data):
    started, release = Event(), Event()
    calls = []

    def cold_read():
        calls.append(True)
        started.set()
        assert release.wait(5)
        return json.dumps([curated_pattern_data]).encode()

    monkeypatch.setenv("DESIGN_MCP_SURFACE", "both")
    monkeypatch.setattr(corpus, "read_corpus", cold_read)
    monkeypatch.setattr(corpus, "cache_path", lambda: pytest.fail("Unexpected cache path lookup"))
    api = runpy.run_module("design_mcp.server", run_name="design_mcp._cold_server", alter_sys=True)
    tools = await api["mcp"].list_tools()
    assert len(tools) == 17 and not calls
    search = asyncio.create_task(api["search_design_patterns"]("dashboard", limit=1))
    other_reader = asyncio.create_task(api["get_design_blueprint"](curated_pattern_data["id"]))
    try:
        assert await asyncio.to_thread(started.wait, 3)
        direction = await api["direct"]("Stage manager turnaround board")
        assert direction["direction"]["id"] == "stage-call-sheet" and not search.done()
    finally:
        release.set()
        matches, blueprint = await asyncio.gather(search, other_reader)
    assert matches[0]["id"] == blueprint["id"] == curated_pattern_data["id"] and len(calls) == 1


@pytest.mark.asyncio
async def test_corrupt_cache_reaches_the_client_and_directions_still_work(tmp_path, monkeypatch):
    from fastmcp import Client

    cache_file = tmp_path / "patterns.json"
    cache_file.write_bytes(b"broken")
    monkeypatch.setenv("DESIGN_MCP_SURFACE", "both")
    monkeypatch.setattr(corpus, "read_bundled", lambda: None)
    monkeypatch.setattr(corpus, "cache_path", lambda: cache_file)
    monkeypatch.setattr(corpus, "_download", lambda: pytest.fail("Unexpected automatic repair"))
    api = runpy.run_module("design_mcp.server", run_name="design_mcp._corrupt_server", alter_sys=True)
    async with Client(api["mcp"]) as client:
        for name, arguments in (("search_design_patterns", {"query": "dashboard"}),
                                ("analyze_and_devibecode", {"source_code": "<main>Board</main>"}),
                                ("get_library_recommendations", {"use_case": "dashboard"})):
            reply = await client.call_tool(name, arguments, raise_on_error=False)
            assert reply.is_error and "doctor --repair" in reply.content[0].text
        direction = await client.call_tool("direct", {"brief": "Stage manager turnaround board"})
        assert direction.structured_content["direction"]["id"] == "stage-call-sheet"
    assert cache_file.read_bytes() == b"broken"


@pytest.mark.parametrize(("mode", "count", "key"), [
    ("both", 17, "direction"), ("legacy", 14, "page_types"), ("v2", 3, "direction"),
])
@pytest.mark.asyncio
async def test_stdio_discovery_annotations_and_call_from_another_directory(tmp_path, monkeypatch, capfd,
                                                                          mode, count, key):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    result = await asyncio.wait_for(doctor._stdio(sys.executable, ["-m", "design_mcp.cli", "serve"], mode), 30)
    report = capfd.readouterr().out
    assert f"{mode}, {count} tools" in report
    assert "PASS stdio initialize" in report and key in result
    assert ("PASS direction annotations" in report) == (mode != "legacy")


def test_doctor_checks_installed_metadata_and_detects_a_shadowed_package(tmp_path, monkeypatch):
    info = tmp_path / "design_mcp-0.1.0.dist-info"
    info.mkdir()
    project = project_metadata()["project"]
    headers = ["Metadata-Version: 2.1", "Name: design-mcp", "Version: 0.1.0",
               f"Requires-Python: {project['requires-python']}"]
    headers.extend(f"Requires-Dist: {req}" for req in project["dependencies"])
    (info / "METADATA").write_text("\n".join(headers) + "\n", encoding="utf-8")
    (info / "entry_points.txt").write_text("[console_scripts]\ndesign-mcp = design_mcp.cli:main\n")
    installed = metadata.distribution
    monkeypatch.setattr(metadata, "distribution",
                        lambda name: metadata.PathDistribution(info) if name == "design-mcp" else installed(name))
    script = tmp_path / "design-mcp"
    script.touch()
    assert "0.1.0" in doctor._installation(script)
    (tmp_path / "design_mcp").mkdir()
    (tmp_path / "design_mcp" / "cli.py").touch()
    with pytest.raises(RuntimeError, match="installation records"):
        doctor._installation(script)


@pytest.mark.asyncio
async def test_curated_default_never_opens_legacy_data(monkeypatch, capsys):
    monkeypatch.delenv("DESIGN_MCP_SURFACE", raising=False)
    monkeypatch.setattr(corpus, "read_corpus", lambda: pytest.fail("Default contacted corpus"))
    monkeypatch.setattr(corpus, "read_bundled", lambda: pytest.fail("Default checked bundled corpus"))
    monkeypatch.setattr(corpus, "cache_path", lambda: pytest.fail("Default checked legacy cache"))
    api = runpy.run_module("design_mcp.server", run_name="design_mcp._default_server", alter_sys=True)
    assert {tool.name for tool in await api["mcp"].list_tools()} == {"direct", "react", "check"}
    result = await api["direct"]("Stage manager turnaround board")
    assert result["direction"]["id"] == "stage-call-sheet"

    async def local_client(command, args, mode):
        assert mode == "v2"
        return "fixture call"

    monkeypatch.setattr(doctor, "_stdio", local_client)
    assert await asyncio.to_thread(doctor.run) == 0
    assert "SKIP legacy corpus and cache" in capsys.readouterr().out


def test_doctor_legacy_cache_is_read_only_and_repair_is_explicit(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DESIGN_MCP_SURFACE", "both")
    payload = b"[]"
    cached = tmp_path / "cache" / "patterns.json"
    monkeypatch.setattr(corpus, "SIZE", len(payload))
    monkeypatch.setattr(corpus, "SHA256", hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(corpus, "cache_path", lambda: cached)
    monkeypatch.setattr(corpus, "read_bundled", lambda: None)
    monkeypatch.setattr(corpus, "_download", lambda: pytest.fail("Plain doctor must work offline"))
    def invoke(*options):
        monkeypatch.setattr(sys, "argv", ["cli.py", "doctor", *options])
        with pytest.raises(SystemExit) as result:
            cli.main()
        return result.value.code

    async def local_client(command, args, mode):
        assert command == sys.executable and args == ["-m", "design_mcp.cli", "serve"]
        return "fixture call"

    monkeypatch.setattr(doctor, "_stdio", local_client)
    assert invoke() == 0
    report = capsys.readouterr().out
    assert "SKIP installed entry point" in report and "SKIP external client" in report
    assert "SKIP legacy cache" in report and not cached.parent.exists()
    cached.parent.mkdir()
    cached.write_bytes(b"xx")
    assert invoke() == 1 and cached.read_bytes() == b"xx"
    assert "FAIL legacy cache" in capsys.readouterr().out
    monkeypatch.setattr(corpus, "read_bundled", lambda: payload)
    assert invoke("--repair") == 0 and cached.read_bytes() == payload
    assert "PASS legacy cache" in capsys.readouterr().out
