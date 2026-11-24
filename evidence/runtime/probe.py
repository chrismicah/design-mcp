"""Read-only runtime probe for Design MCP at the checked-out commit.

Usage: <python-with-fastmcp> probe.py <label> <outdir>
Imports whichever `design_mcp` is first on sys.path (set PYTHONPATH to the
worktree for the source build; leave unset for the installed build).
Writes one JSON file per tool call plus summary.json. Writes nothing to the repo.
"""
import asyncio, hashlib, inspect, json, re, sys, tempfile, time
from pathlib import Path

label, outdir = sys.argv[1], Path(sys.argv[2])
outdir.mkdir(parents=True, exist_ok=True)

t0 = time.time()
import design_mcp, design_mcp.server as S
import_s = round(time.time() - t0, 2)

TELLS = {
    "font_inter": r"\bInter\b", "font_roboto": r"\bRoboto\b",
    "font_space_grotesk": r"Space Grotesk", "font_system_ui": r"system-ui",
    "glass": r"glassmorph|backdrop-blur|backdrop-filter",
    "gradient": r"gradient", "purple_indigo_violet": r"purple|indigo|violet|#6366f1|#8b5cf6|#7c3aed",
    "startup_blue": r"#3b82f6|#2563eb|blue-500|blue-600",
    "rounded_card": r"rounded-(xl|2xl|lg)|border-radius:\s*1[26]px",
    "soft_shadow": r"shadow-(sm|md|lg|xl)",
    "copy_get_started": r"Get started|Get Started", "copy_elevate": r"Elevate|Seamless|Unlock|Supercharge",
    "centered": r"text-center|mx-auto|hero_centered|centered",
    "three_col_grid": r"grid-cols-3|3-column|three-column",
}
GOOD = {
    "display_serif": r"Fraunces|Newsreader|Playfair|Instrument Serif|GT Sectra|Canela|Tiempos",
    "workhorse": r"Archivo|General Sans|Instrument Sans|S[oö]hne|Geist",
    "tracking": r"letter-spacing|tracking-",
    "reduced_motion": r"prefers-reduced-motion",
    "asymmetry": r"asymmetr|offset|overlap|full-bleed|full_bleed",
    "why": r"\bwhy\b|rationale|because",
}

def sweep(text, table):
    return {k: len(re.findall(v, text)) for k, v in table.items() if re.search(v, text)}

def fn(name):
    t = getattr(S, name)
    return getattr(t, "fn", t)

summary = {"label": label, "module_file": design_mcp.__file__, "version": getattr(design_mcp, "__version__", None),
           "server_sha256": hashlib.sha256(Path(S.__file__).read_bytes()).hexdigest()[:16],
           "import_seconds": import_s, "pattern_count": S.db.count(), "calls": {}}

async def call(key, name, **kw):
    t = time.time()
    try:
        out = await fn(name)(**kw)
        err = None
    except Exception as e:  # recorded, never hidden
        out, err = None, f"{type(e).__name__}: {e}"
    text = json.dumps(out, default=str)
    (outdir / f"{key}.json").write_text(json.dumps({"tool": name, "args": kw, "error": err, "result": out}, indent=1, default=str))
    rec = {"tool": name, "bytes": len(text), "approx_tokens": len(text) // 4, "ms": round((time.time() - t) * 1000),
           "error": err, "tells": sweep(text, TELLS), "good": sweep(text, GOOD)}
    summary["calls"][key] = rec
    return out

BRIEFS = {
    "landing": ("landing page for a specialty coffee roaster", "Landing Page"),
    "dashboard": ("analytics dashboard for a logistics company", "Dashboard"),
    "mobile": ("mobile banking app home screen", "Home"),
    "portfolio": ("portfolio for an architecture photographer", "Portfolio"),
    "pricing": ("SaaS pricing page", "Pricing"),
    "editorial": ("editorial magazine site about food", "Blog"),
}
SLOP = '''
export default function Hero() {
  return (
    <div className="bg-gradient-to-r from-purple-600 to-blue-500 text-center py-20" style={{fontFamily: "Inter, system-ui"}}>
      <p className="uppercase tracking-widest text-sm">INTRODUCING ACME</p>
      <h1 className="text-6xl font-bold">Elevate your workflow</h1>
      <p className="text-gray-200">Seamless collaboration to supercharge your team!</p>
      <button className="bg-blue-500 rounded-2xl shadow-lg px-6 py-3">Get started</button>
      <button className="rounded-2xl border px-6 py-3">Learn more</button>
      <div className="grid grid-cols-3 gap-8 mt-16">
        {[1,2,3].map(i => <div key={i} className="bg-white rounded-2xl shadow-md p-6"><span>🚀</span><h3 className="font-bold">Feature</h3><p>Text</p></div>)}
      </div>
      <nav className="backdrop-blur-md bg-white/30 fixed top-0">Nav</nav>
    </div>
  )
}
'''

async def main():
    # --- inventory -----------------------------------------------------
    tools = await S.mcp.get_tools() if hasattr(S.mcp, "get_tools") else {}
    inv = {}
    for name, t in tools.items():
        f = getattr(t, "fn", t)
        sig = inspect.signature(f)
        params = getattr(t, "parameters", None)
        inv[name] = {"params": list(sig.parameters), "required": [p for p, v in sig.parameters.items() if v.default is inspect._empty],
                     "doc_chars": len(f.__doc__ or ""), "schema_chars": len(json.dumps(params, default=str)) if params else None}
    summary["inventory"] = inv
    summary["inventory_total_chars"] = sum((v["doc_chars"] + (v["schema_chars"] or 0)) for v in inv.values())

    # --- search / ranking ---------------------------------------------
    rank = {}
    for k, (q, pt) in BRIEFS.items():
        res = await call(f"search_{k}", "search_design_patterns", query=q)
        res2 = await fn("search_design_patterns")(query=q)
        # recompute score distribution exactly as database.search does
        words = q.lower().split()
        scores = []
        for p in S.db._patterns:
            if p.platform.value != "web":
                continue
            hay = (f"{p.name} {p.page_type} {' '.join(p.tags)} {' '.join(p.ux_patterns)} {' '.join(p.ui_elements)} "
                   f"{p.industry or ''} {p.behavioral_description or ''}").lower()
            scores.append(sum(1 for w in words if w in hay))
        top = max(scores) if scores else 0
        rank[k] = {"query": q, "returned": [(r.get("id"), r.get("name"), r.get("page_type"), r.get("source") if isinstance(r, dict) else None) for r in (res or [])],
                   "deterministic": res == res2, "max_score": top, "n_words": len(words),
                   "candidates_at_max_score": scores.count(top), "candidates_score_gt0": sum(1 for s in scores if s > 0),
                   "web_candidates": len(scores),
                   "distinct_fonts_in_results": sorted({m for r in (res or []) for m in re.findall(r"font-family[^,;}\"]*|\"font[^\"]*\":\s*\"([^\"]+)\"", json.dumps(r))})[:12],
                   "result_keys": sorted(res[0].keys()) if res else []}
        await call(f"search_{k}_typed", "search_design_patterns", query=q, page_type=pt)
    rank["mobile_ios"] = [(r.get("id"), r.get("name")) for r in (await call("search_mobile_ios", "search_design_patterns", query="mobile banking app home screen", platform="ios") or [])]
    rank["stopword_only"] = [(r.get("id"), r.get("name")) for r in (await call("search_stopword", "search_design_patterns", query="a") or [])]
    rank["nonsense"] = len(await call("search_nonsense", "search_design_patterns", query="zzqx vorpal") or [])
    rank["vague"] = [(r.get("id"), r.get("name"), r.get("page_type")) for r in (await call("search_vague", "search_design_patterns", query="make it look nice") or [])]
    summary["ranking"] = rank

    first = (await fn("search_design_patterns")(query="dashboard"))[0]["id"]
    await call("blueprint_condensed", "get_design_blueprint", pattern_id=first)
    await call("blueprint_detailed", "get_design_blueprint", pattern_id=first, detailed=True)
    await call("blueprint_missing", "get_design_blueprint", pattern_id="nope")

    # --- tokens ---------------------------------------------------------
    a = await call("tokens_default", "get_semantic_tokens")
    b = await call("tokens_primary_red", "get_semantic_tokens", primary_color="#c2410c", color_mode="light")
    c = await call("tokens_primary_green", "get_semantic_tokens", primary_color="#14532d", color_mode="light")
    summary["tokens"] = {"primary_color_changes_output": json.dumps(b) != json.dumps(c),
                         "primary_color_ignored_equals_default": json.dumps(b) == json.dumps(a),
                         "wcag_flag_present": isinstance(b, dict) and b.get("wcag_aa_verified")}
    for st in ("light", "dark", "brand", "minimal", "bold"):
        await call(f"tokens_style_{st}", "get_semantic_tokens", style=st)
    styles = {st: json.dumps(json.loads((outdir / f"tokens_style_{st}.json").read_text())["result"], sort_keys=True) for st in ("brand", "minimal", "bold")}
    summary["tokens"]["brand_minimal_bold_identical"] = len(set(styles.values())) == 1

    tax = await call("taxonomy", "get_design_taxonomy")
    summary["taxonomy_keys"] = {k: (len(v) if hasattr(v, "__len__") else v) for k, v in (tax or {}).items()}
    for n in ("empty_state", "skeleton_loading", "error_handling", "onboarding_flow", "form_validation", "infinite_scroll", "hero"):
        await call(f"behavior_{n}", "get_behavioral_pattern", pattern_name=n)
    summary["behavior_documented_names_resolve"] = {n: "error" not in json.loads((outdir / f"behavior_{n}.json").read_text())["result"] for n in ("empty_state", "skeleton_loading", "error_handling", "onboarding_flow", "form_validation", "infinite_scroll")}
    await call("compare_pricing", "compare_design_approaches", page_type="Pricing")
    await call("compare_lowercase_plural", "compare_design_approaches", page_type="pricing pages")

    # --- design system / recipes: the "one call" candidates -------------
    ds = {}
    for pt in ("Dashboard", "Landing Page", "Pricing", "Portfolio", "Blog", "Mobile App"):
        for mode in ("dark", "light"):
            out = await call(f"system_{pt.replace(' ', '_')}_{mode}", "get_design_system", page_type=pt, color_mode=mode)
            ds[f"{pt}/{mode}"] = hashlib.sha256(json.dumps(out, sort_keys=True, default=str).encode()).hexdigest()[:10]
    summary["design_system_distinct_outputs"] = {"calls": len(ds), "distinct": len(set(ds.values())), "hashes": ds}
    for aes in ("editorial", "brutalist", "luxury", "playful"):
        await call(f"system_aesthetic_{aes}", "get_design_system", page_type="Landing Page", color_mode="light", aesthetic=aes)
    rec = {}
    lst = await call("recipe_list", "get_visual_recipe")
    for pt in ("Dashboard", "Landing Page", "Pricing", "Portfolio", "Blog", "Mobile App"):
        out = await call(f"recipe_{pt.replace(' ', '_')}", "get_visual_recipe", page_type=pt)
        rec[pt] = hashlib.sha256(json.dumps(out, sort_keys=True, default=str).encode()).hexdigest()[:10]
    summary["recipe_distinct_outputs"] = {"calls": len(rec), "distinct": len(set(rec.values())), "hashes": rec}

    # --- critique path on a deliberately banned-tell sample ---------------
    await call("devibecode_slop", "analyze_and_devibecode", source_code=SLOP)
    await call("visual_suggestions_slop", "get_visual_suggestions", source_code=SLOP)
    await call("refactor_slop", "generate_refactored_code", source_code=SLOP)
    crit = json.dumps([json.loads((outdir / f"{k}.json").read_text())["result"] for k in ("devibecode_slop", "visual_suggestions_slop")], default=str).lower()
    summary["slop_sample_detection"] = {t: (t_word in crit) for t, t_word in {
        "inter_font": "inter", "system_ui": "system-ui", "purple_blue_gradient": "gradient", "centered_hero": "center",
        "three_card_grid": "grid", "rounded_shadow_cards": "shadow", "glass_nav": "backdrop", "elevate_copy": "elevate",
        "get_started_copy": "get started", "emoji_bullet": "emoji", "exclamation_cta": "exclamation", "eyebrow_allcaps": "uppercase"}.items()}

    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "Hero.tsx").write_text(SLOP)
        await call("scan_tmp_project", "scan_project", project_path=d)
    await call("scan_missing_path", "scan_project", project_path="/nonexistent/zz")

    await call("libs_default", "get_library_recommendations", use_case="marketing landing page")
    await call("libs_charts", "get_library_recommendations", use_case="dashboard", needs_charts=True)
    await call("lib_details", "get_library_details", library_name="shadcn-ui")
    await call("lib_details_missing", "get_library_details", library_name="nope")

    summary["errors"] = {k: v["error"] for k, v in summary["calls"].items() if v["error"]}
    summary["total_seconds"] = round(time.time() - t0, 2)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1, default=str))

asyncio.run(main())
s = summary
print(json.dumps({k: s[k] for k in ("label", "module_file", "version", "server_sha256", "import_seconds", "pattern_count", "inventory_total_chars", "tokens", "behavior_documented_names_resolve", "design_system_distinct_outputs", "recipe_distinct_outputs", "slop_sample_detection", "errors", "total_seconds")}, indent=1, default=str))
