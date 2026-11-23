"""Local install and stdio diagnostics for the interpreter running this command."""

import asyncio
from importlib import metadata, resources
import os
from pathlib import Path
import sys

from . import DEFAULT_SURFACE


DIRECTION_TOOLS = {"direct", "react", "check", "get_component_pattern"}
LEGACY_TOOLS = {
    "search_design_patterns", "get_design_blueprint", "get_semantic_tokens", "get_design_taxonomy",
    "get_behavioral_pattern", "compare_design_approaches", "analyze_and_devibecode", "get_design_system",
    "get_library_recommendations", "get_library_details", "scan_project", "generate_refactored_code",
    "get_visual_recipe", "get_visual_suggestions",
}


def _interpreter():
    if sys.version_info < (3, 10):
        raise RuntimeError(f"{sys.executable} requires Python 3.10 or later to run design-mcp.")
    return f"{sys.version.split()[0]} at {sys.executable}"


def _dependencies():
    from packaging.specifiers import SpecifierSet

    dist = metadata.distribution("fastmcp")
    required = dist.metadata["Requires-Python"]
    if sys.version.split()[0] not in SpecifierSet(required):
        raise RuntimeError(f"FastMCP {dist.version} requires Python {required}.")
    return f"FastMCP {dist.version} (Python {required}), MCP {metadata.version('mcp')}"


def _installation(script):
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet
    from .cli import main

    dist = metadata.distribution("design-mcp")
    entries = dist.entry_points.select(group="console_scripts", name="design-mcp")
    if not script.is_file() or len(entries) != 1:
        raise RuntimeError(f"Missing or incorrect console entry point at {script}. Reinstall design-mcp.")
    entry = next(iter(entries))
    if entry.value != "design_mcp.cli:main" or entry.load() is not main:
        raise RuntimeError(f"Unexpected installed entry point {entry.value}. Reinstall design-mcp.")
    recorded = dist.locate_file("design_mcp/cli.py")
    active = resources.files("design_mcp") / "cli.py"
    if isinstance(recorded, Path) and recorded.is_file() and recorded.resolve() != Path(str(active)).resolve():
        raise RuntimeError(f"Loaded {active}, but the installation records {recorded}.")
    if sys.version.split()[0] not in SpecifierSet(dist.metadata["Requires-Python"]):
        raise RuntimeError(f"The installed design-mcp requires Python {dist.metadata['Requires-Python']}.")
    for entry in dist.requires or ():
        requirement = Requirement(entry)
        if requirement.marker and not requirement.marker.evaluate():
            continue
        installed = metadata.version(requirement.name)
        if installed not in requirement.specifier:
            raise RuntimeError(f"Installed {requirement.name} {installed} does not satisfy {requirement}.")
    return f"design-mcp {dist.version} at {script}"


def _directions():
    from .direction_records import library
    return f"{len(library())} validated directions in {resources.files('design_mcp')}"


def _references():
    from .resources import read_json

    names = (
        "tokens/token_sets.json", "tokens/semantic_tokens.json", "decision_trees_indexed.json",
        "anti_pattern_fixes.json", "visual_recipes.json", "anti_generic_system.json", "libraries.json",
        "layout_templates.json", "behavioral_templates.json", "component_code.json", "taxonomy.json",
    )
    for name in names:
        expected = list if name in {"tokens/token_sets.json", "decision_trees_indexed.json"} else dict
        data = read_json(name)
        if not isinstance(data, expected) or not data:
            raise ValueError(f"Expected a nonempty {expected.__name__} in data/{name}. Reinstall design-mcp.")
    return f"{len(names)} legacy reference files"


def _bundled_corpus():
    from . import corpus
    if corpus.read_bundled() is not None:
        return f"{corpus.SIZE} bytes, SHA-256 {corpus.SHA256}"
    print("SKIP bundled corpus — optional in this installation")


def _legacy_cache(repair):
    from . import corpus
    data = corpus.ensure_cache(repair=True) if repair else corpus.read_cached()
    if data is not None:
        return f"SHA-256 {corpus.SHA256} at {corpus.cache_path()}"
    print(f"SKIP legacy cache — empty at {corpus.cache_path()} (available on demand)")


async def _stdio(command, args, mode):
    from mcp import ClientSession, StdioServerParameters, stdio_client

    if mode not in {"legacy", "both", "v2"}:
        raise ValueError("DESIGN_MCP_SURFACE must be legacy, both, or v2.")
    env = {"DESIGN_MCP_SURFACE": mode, "FASTMCP_SHOW_SERVER_BANNER": "false",
           "FASTMCP_ENV_FILE": os.devnull, "FASTMCP_TELEMETRY_MODE": "off",
           "PYTHONDONTWRITEBYTECODE": "1"}
    if "PYTHONPATH" in os.environ:
        env["PYTHONPATH"] = os.environ["PYTHONPATH"]
    params = StdioServerParameters(command=command, args=args, env=env)
    expected = {"legacy": LEGACY_TOOLS, "v2": DIRECTION_TOOLS, "both": LEGACY_TOOLS | DIRECTION_TOOLS}[mode]
    async with stdio_client(params, errlog=sys.stderr) as (reader, writer), ClientSession(reader, writer) as client:
        hello = await client.initialize()
        if hello.server_info.name != "DesignIntelligence":
            raise ValueError(f"Unexpected stdio server {hello.server_info.name!r}.")
        print(f"PASS stdio initialize — {hello.server_info.name}, protocol {hello.protocol_version}")
        tools = (await client.list_tools()).tools
        names = {tool.name for tool in tools}
        if names != expected or len(tools) != len(expected):
            raise ValueError(f"Unexpected tools for {mode}. Received {sorted(tool.name for tool in tools)}.")
        print(f"PASS stdio tools/list — {mode}, {len(tools)} tools")
        for tool in tools:
            if tool.name in DIRECTION_TOOLS:
                hints = tool.annotations.model_dump(by_alias=True) if tool.annotations else {}
                for key, value in (("readOnlyHint", True), ("destructiveHint", False),
                                   ("idempotentHint", True), ("openWorldHint", False)):
                    if hints.get(key) is not value:
                        raise ValueError(f"{tool.name} has an incorrect {key} annotation.")
        if mode != "legacy":
            print("PASS direction annotations — direct, react, check, get_component_pattern")
            name, arguments, key = "direct", {"brief": "Mobile train ticket", "surface": "mobile"}, "direction"
        else:
            name, arguments, key = "get_design_taxonomy", {}, "page_types"
        reply = await client.call_tool(name, arguments)
        if reply.is_error or not (reply.structured_content or {}).get(key):
            raise ValueError(f"{name} did not return its expected structured result.")
    return f"{name} returned {key}"


def _reason(error):
    causes = getattr(error, "exceptions", ())
    return " | ".join(_reason(cause) for cause in causes) if causes else str(error) or type(error).__name__


def run(*, repair: bool = False) -> int:
    failed = False

    def check(label, action):
        nonlocal failed
        try:
            detail = action()
            if detail is not None:
                print(f"PASS {label} — {detail}")
        except Exception as error:
            failed = True
            print(f"FAIL {label} — {_reason(error)}")

    check("interpreter", _interpreter)
    check("FastMCP interpreter compatibility", _dependencies)
    script = Path(sys.argv[0]).absolute()
    if script.name in {"design-mcp", "design-mcp.exe"}:
        check("installed entry point", lambda: _installation(script))
        command, args = str(script), ["serve"]
    else:
        print("SKIP installed entry point — invoked as a Python module")
        command, args = sys.executable, ["-m", "design_mcp.cli", "serve"]
    check("bundled directions", _directions)
    check("bundled references", _references)
    mode = os.environ.get("DESIGN_MCP_SURFACE", DEFAULT_SURFACE).strip().lower()
    if repair or mode in {"legacy", "both"}:
        check("bundled corpus", _bundled_corpus)
        check("legacy cache", lambda: _legacy_cache(repair))
    else:
        print("SKIP legacy corpus and cache — use doctor --repair to prepare the legacy cache")
    check("stdio tools/call", lambda: asyncio.run(asyncio.wait_for(_stdio(command, args, mode), timeout=30)))
    print("SKIP external client — a model session in your configured client is a separate check")
    return int(failed)
