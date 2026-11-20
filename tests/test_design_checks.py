from pathlib import Path

from design_mcp.design_checks import inspect_design


def rules(code):
    return {item["rule"] for item in inspect_design(code)}


def test_rejects_composition_and_visible_tells():
    code = """<style>
body { font-family: Inter, serif; background:linear-gradient(purple, blue); }
nav { backdrop-filter: blur(10px); }
.card { border-radius: 16px; box-shadow: 0 3px gray; }
button { background-color: #3b82f6; }
section { animation: fadeUp 250ms; }
</style>
<header class="text-center"><span class="uppercase">FOR TEAMS</span>
<h1>Reports</h1><p>Seamless work</p><div><button>Get started</button><a>Try!</a></div></header>
<div class="grid grid-cols-3"><div class="rounded-2xl card"></div><div class="rounded-2xl card"></div><div class="rounded-2xl card"></div></div>
<ul><li>🚀 Reports</li></ul>"""
    assert {
        "brand-font", "purple-blue-gradient", "glass-nav", "rounded-shadow", "startup-blue",
        "default-fade-up", "centered-hero", "generic-copy", "generic-cta", "exclamation-cta",
        "symmetric-cards", "emoji-bullet",
    } <= rules(code)


def test_source_checks_have_locations_and_ignore_comments_and_fallbacks():
    code = """<!-- font-family: Inter -->
<style>body{font-family: Archivo, system-ui;} main{font-family: 'Space Grotesk', serif;}</style>
<main><button>Unlock account</button><ul><li>Fresh arrivals</li></ul></main>"""
    assert inspect_design(code) == [
        {"rule": "brand-font", "line": 2, "detail": "Primary font uses Space Grotesk."},
    ]


def test_trackr_is_a_negative_fixture():
    fixture = Path(__file__).resolve().parents[1] / "test_trackr_v3.html"
    assert "brand-font" in rules(fixture.read_text(encoding="utf-8-sig"))


def test_catches_variable_shorthand_jsx_and_hue_tells():
    probes = [
        ':root{--project-font:Inter} body{font-family:var(--project-font)}',
        'body{font:16px/1.5 Roboto, sans-serif}',
        "<h1 style={{fontFamily: 'Inter'}} >Reports</h1>",
    ]
    assert all("brand-font" in rules(probe) for probe in probes)
    assert "brand-font" not in rules('body{font-family:"Inter Tight", serif}')
    assert "purple-blue-gradient" in rules('body{background:linear-gradient(135deg,#667eea,#764ba2)}')
    assert "generic-copy" in rules('<h1>Now elevate your roast</h1>')
