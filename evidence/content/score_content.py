#!/usr/bin/env python3
"""Reproducible content audit for the Design MCP pattern corpus.

Reads EVERY record in the runtime data dir (design_mcp/data) and verifies the
root mirror (data/) is byte-identical. Scores each record 0-4 on five axes using
the written rubric in CONTENT-AUDIT.md, then emits row-level CSVs, a
distribution JSON and an SVG chart. Heuristic only: no model calls, no network.

Usage:  python3 -I evidence/content/score_content.py [repo_root]
"""
import csv, hashlib, json, re, sys, collections as C
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2])
RT, MIRROR, OUT = ROOT / "design_mcp/data", ROOT / "data", ROOT / "evidence/content"

def load(rel): return json.loads((RT / rel).read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

# ---- rubric constants (documented in CONTENT-AUDIT.md §2) -------------------
SOURCE_TASTE_PRIOR = {  # comparison column ONLY; not used in any score or action
   "curated": 3, "awwwards": 3, "landbook": 2, "dribbble": 2, "webui-7kbal": 1}
JUNK_NAME = re.compile(
    r"^(40[0-9]|50[0-9])\b|\b(40[134]|50[0-4])\b.*(not found|forbidden|error|gateway|unavailable)|"
    r"not found|forbidden|access denied|bad gateway|attention required|cloudflare|just a moment|"
    r"未被授权|页面不存在|page not found|account suspended|default (web )?site|index of /|"
    r"welcome to nginx|domain .*for sale|this site can.t be reached|under construction|^error$|^untitled$", re.I)
HASH_NAME = re.compile(r"^[0-9a-f]{10,}$", re.I)  # dribbble hex-id names carry no meaning
PLACEHOLDER = re.compile(r"^\[(template|component):[^\]]+\]$")
BANNED = {  # banned-tells list from the owner brief, as greppable phrases
    "font:inter": r"\binter\b", "font:roboto": r"\broboto\b", "font:space-grotesk": r"space grotesk",
    "font:system-ui": r"system-ui", "hero:centered": r"text-center|centered (hero|headline)",
    "hero:headline+subtext+cta": r"large headline with subtext and primary cta",
    "motion:stagger-fade": r"fade-in animations?.*stagger|staggered by \d+ms",
    "motion:hover-glow": r"glow", "surface:glass": r"glass(morphism)?|backdrop-blur",
    "color:gradient-heavy": r"gradient-heavy|purple.*gradient|gradient.*purple",
    "color:indigo-500": r"#6366f1", "color:blue-500": r"#3b82f6", "color:violet-500": r"#8b5cf6",
    "copy:generic-cta": r"get started|elevate your|seamless|unlock|supercharge",
    "copy:placeholder": r"your headline here|compelling subheadline|\bheadline\b</h1>|lorem ipsum",
    "layout:3-4-card-grid": r"grid-cols-(3|4)\b|three (feature )?cards|3-column feature",
    "card:rounded-shadow": r"rounded-(xl|2xl)[^\"]*shadow|shadow[^\"]*rounded-(xl|2xl)",
}
BANNED_RE = {k: re.compile(v, re.I) for k, v in BANNED.items()}
INVALID_HEX = re.compile(r"#(?![0-9a-fA-F]{3,8}\b)[A-Za-z][\w-]*")  # e.g. "#zinc-200"

DIRECTION = {  # required art-direction fields from the owner brief
    "type-pairing": re.compile(r"display.{0,40}(serif|font)|font.{0,20}pair|(fraunces|newsreader|playfair|archivo|instrument sans|general sans)", re.I),
    "scale-ratio": re.compile(r"ratio|scale.{0,15}\d(\.\d+)?x|text-\[\d", re.I),
    "palette-logic": re.compile(r"#[0-9a-f]{6}.{0,80}(accent|ink|paper|surface)", re.I),
    "layout-skeleton": re.compile(r"grid|col-span|column|sidebar|full-bleed|split", re.I),
    "motion-spec": re.compile(r"\d+ms|ease|transition|prefers-reduced-motion", re.I),
    "why": re.compile(r'"_?why"|because|so that', re.I)}

def tells(text):
    return sorted(k for k, rx in BANNED_RE.items() if rx.search(text))

def band(n):  # share count -> distinctiveness of a text field
    return 4 if n == 1 else 3 if n <= 10 else 2 if n <= 100 else 1 if n <= 1000 else 0

def clamp(x): return max(0, min(4, x))

# ---- patterns ---------------------------------------------------------------
def score_patterns(rows, token_sets):
    desc_n = C.Counter(r["behavioral_description"] for r in rows)
    url_n = C.Counter(r.get("source_url") for r in rows)
    tok_n = C.Counter(r.get("semantic_tokens") for r in rows)
    name_seen, out = {}, []
    CONCRETE = re.compile(r"\d+(\.\d+)?(px|rem|em|ms|%)|\d+/\d+|-0\.\d+em", re.I)
    for r in rows:
        name = r["name"].strip()
        ln = r.get("layout_notes") or ""
        ln_real = bool(ln) and not PLACEHOLDER.match(ln)
        hints = r.get("component_hints") or []
        # a hint is real only if it carries non-empty, non-placeholder code
        hints_real = sum(1 for h in hints if (h.get("code") or "").strip() and not PLACEHOLDER.match(h["code"].strip()))
        img = r.get("image_url") or ""
        asset_ref = bool(img)
        local_img = asset_ref and not img.startswith("http")
        asset_state = ("local-present" if (ROOT / img).is_file() else "local-absent") if local_img else \
                      ("remote-unverified" if asset_ref else "none")  # remote URLs are NOT fetched or counted present
        # source-agnostic: error/blocked page titles with no design asset behind them
        junk = bool(JUNK_NAME.search(name)) and not asset_ref
        opaque = bool(HASH_NAME.search(name))
        tk = r.get("semantic_tokens")
        tset = token_sets[tk] if isinstance(tk, int) and 0 <= tk < len(token_sets) else {}
        dn = desc_n[r["behavioral_description"]]
        own_desc = r["behavioral_description"] if dn <= 10 else ""
        # entry-specific text vs inherited template text: tells are judged in context
        own_text = " ".join([own_desc, ln if ln_real else "", json.dumps(r.get("primary_colors") or [])])
        inherited = " ".join([r["behavioral_description"] if dn > 10 else "", json.dumps(tset) if tok_n[tk] > 10 else ""])
        t_own, t_inh = tells(own_text), [x for x in tells(inherited) if x not in tells(own_text)]
        t = t_own + t_inh
        key = re.sub(r"\W+", "", name.lower())
        dup_of = name_seen.get(key) if asset_ref else None  # duplicates judged only among asset-backed rows
        if asset_ref: name_seen.setdefault(key, r["id"])
        url_dup = url_n[r.get("source_url")] > 1

        D = band(dn) + (1 if r.get("primary_colors") else 0) + (1 if r.get("visual_style") else 0) \
            - (1 if tok_n[tk] > 1000 else 0)
        # craft evidence available WITHOUT pixels: concrete entry-specific choices only
        craft = (1 if ln_real and CONCRETE.search(ln) else 0) + (1 if r.get("primary_colors") else 0) \
            + (1 if r.get("ux_patterns") else 0) + (1 if own_desc and CONCRETE.search(own_desc) else 0)
        if craft == 0:
            T, taste_basis = "", "unknown-no-pixels" if asset_ref else "unknown-no-evidence"
        else:
            T, taste_basis = clamp(craft - len(t_own)), "entry-text"
        U = (1 if ln_real else 0) + (1 if r.get("ux_patterns") else 0) + (1 if r.get("primary_colors") else 0) \
            + (1 if asset_state == "local-present" else 0) + (1 if hints_real else 0) + (1 if dn <= 10 else 0)
        fields = ["behavioral_description", "ui_elements", "industry", "layout_type", "visual_style",
                  "color_mode", "primary_colors", "ux_patterns", "accessibility_notes"]
        filled = sum(1 for f in fields if r.get(f)) + ln_real + bool(hints_real) + (asset_state == "local-present")
        Cm = round(4 * filled / (len(fields) + 3))
        if junk: D = U = Cm = 0
        D, U, Cm = map(clamp, (D, U, Cm))

        reasons = []
        if junk: reasons.append("junk-page-name")
        if dup_of: reasons.append(f"duplicate-name-of:{dup_of}")
        if url_dup: reasons.append("duplicate-source-url")
        if dn > 100: reasons.append(f"template-description-x{dn}")
        if PLACEHOLDER.match(ln or "x"): reasons.append("placeholder-layout-notes")
        if hints and not hints_real: reasons.append("hints-without-code")
        reasons.append(f"asset:{asset_state}")
        if opaque: reasons.append("opaque-name")
        if not asset_ref and str(r.get("source_url", "")).startswith("http"): reasons.append("page-url-only-recapture-possible")
        if tok_n[tk] > 1000: reasons.append(f"shared-token-set-{tk}-x{tok_n[tk]}")
        if t_own: reasons.append("own-tells:" + "|".join(t_own))
        if t_inh: reasons.append("inherited-tells:" + "|".join(t_inh))
        reasons.append("missing-direction-fields:type-pairing|scale-ratio|motion-spec|why")  # absent from schema

        # disposition: no source or ID priors; nothing is promoted to launch-ready by heuristic
        if junk: action, K = "cull", 0
        elif dup_of: action, K = "merge-duplicate", 2
        elif asset_ref and opaque and asset_state != "local-present" and craft == 0:
            action, K = "cull-unless-blob-recovered", 1
        elif asset_ref: action, K = "rewrite-from-source", 2
        elif craft >= 2: action, K = "keep-as-reference", 2
        elif craft == 1 and not url_dup: action, K = "rewrite", 1
        else: action, K = "cull", 1
        out.append(dict(id=r["id"], source=r["source"], name=" ".join(name.split())[:80], page_type=r["page_type"],
                        distinctiveness=D, taste=T, taste_basis=taste_basis, craft_evidence=craft,
                        usefulness=U, completeness=Cm, ad_keep=K, action=action, desc_share=dn,
                        tells=len(t), asset_state=asset_state, reasons=";".join(reasons),
                        source_prior_rank_comparison_only=SOURCE_TASTE_PRIOR.get(r["source"], 1),
                        orig_quality_score=r.get("quality_score")))
    return out

# ---- supplemental libraries -------------------------------------------------
def flatten_supplemental():
    recs = []
    def add(file, key, obj, kind):
        recs.append((file, key, kind, json.dumps(obj, ensure_ascii=False)))
    for k, v in load("behavioral_templates.json").items(): add("behavioral_templates.json", k, v, "page-template")
    for k, v in load("component_code.json").items(): add("component_code.json", k, v, "component")
    for k, v in load("layout_templates.json").items(): add("layout_templates.json", k, v, "layout")
    for i, v in enumerate(load("tokens/token_sets.json")): add("tokens/token_sets.json", str(i), v, "token-set")
    for k, v in load("tokens/semantic_tokens.json").items(): add("tokens/semantic_tokens.json", k, v, "token-set")
    for k, v in load("visual_recipes.json").items(): add("visual_recipes.json", k, v, "recipe")
    ag = load("anti_generic_system.json")
    for k, v in ag.items():
        if k == "aesthetic_profiles":
            for pk, pv in v.items():
                if not pk.startswith("_"): add("anti_generic_system.json", f"aesthetic_profiles.{pk}", pv, "profile")
        elif k == "global_anti_patterns":
            for i, pv in enumerate(v.get("patterns", [])): add("anti_generic_system.json", f"anti_pattern.{pv.get('name', i)}", pv, "anti-pattern")
        elif k == "component_code":
            for ck, cv in v.items():
                if not ck.startswith("_"): add("anti_generic_system.json", f"component_code.{ck}", cv, "component")
        else: add("anti_generic_system.json", k, v, "system-section")
    for k, v in load("anti_pattern_fixes.json").items(): add("anti_pattern_fixes.json", k, v, "code-fix")
    for k, v in load("decision_trees.json").items(): add("decision_trees.json", k, v, "decision-tree")
    for i, v in enumerate(load("decision_trees_indexed.json")): add("decision_trees_indexed.json", str(i), v, "decision-tree")
    for v in load("libraries.json")["libraries"]: add("libraries.json", v["id"], v, "library")
    for k, v in load("taxonomy.json").items(): add("taxonomy.json", k, v, "taxonomy")
    return recs

def score_supplemental(recs, token_use):
    body_n = C.Counter(b for *_, b in recs)
    out = []
    for file, key, kind, body in recs:
        t = tells(body)
        bad_hex = sorted(set(INVALID_HEX.findall(body)))
        size = len(body)
        concrete = len(re.findall(r"#[0-9a-fA-F]{6}\b|\d+(\.\d+)?(px|rem|em|ms)\b|-0\.\d+em", body))
        why = bool(re.search(r'"_?why"|because|so that', body, re.I))
        D = clamp((3 if body_n[body] == 1 else 0) + (1 if concrete >= 8 else 0) - (1 if len(t) >= 3 else 0))
        T = clamp(3 - len([x for x in t if not x.startswith("color:blue")]) + (1 if why else 0) - (1 if bad_hex else 0))
        U = clamp((2 if concrete >= 4 else 1 if concrete else 0) + (1 if size > 300 else 0) + (1 if why else 0))
        Cm = clamp(1 + (size > 200) + (size > 800) + why)
        use = token_use.get(key, "") if kind == "token-set" and file.endswith("token_sets.json") else ""
        if kind == "library": action = "keep-as-reference"
        elif kind == "token-set" and file.endswith("token_sets.json"):
            # verified: all 141 sets share ONE identical type scale, spacing and radius and carry
            # no font family; only colours vary -> palette is data, not art direction
            action = "rewrite"; t = t + ["scale:identical-across-141-sets"]
        elif T <= 1 or "copy:placeholder" in t or "hero:centered" in t: action = "rewrite"
        elif D >= 3 and T >= 3 and U >= 3: action = "keep-as-reference"  # never launch-ready by heuristic
        else: action = "rewrite"
        K = {"keep-as-reference": 2, "rewrite": 1}[action]
        dirs = [k for k, rx in DIRECTION.items() if rx.search(body)]
        out.append(dict(file=file, key=key, kind=kind, distinctiveness=D, taste=T, usefulness=U,
                        completeness=Cm, ad_keep=K, action=action, tells="|".join(t),
                        direction_fields="|".join(dirs), missing_direction="|".join(k for k in DIRECTION if k not in dirs),
                        invalid_hex="|".join(bad_hex), concrete_values=concrete, chars=size,
                        pattern_refs=use))
    return out

# ---- chart ------------------------------------------------------------------
def svg_chart(dist, path):
    axes = ["distinctiveness", "taste", "usefulness", "completeness", "ad_keep"]
    W, H, pad, bw = 760, 300, 40, 26
    ink, paper = "#1b1b1b", "#f6f3ee"
    shades = ["#c8beb2", "#a8998a", "#7d6e60", "#544638", "#2b2018"]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H+70}" font-family="Georgia,serif">',
         f'<rect width="100%" height="100%" fill="{paper}"/>',
         f'<text x="{pad}" y="24" font-size="15" fill="{ink}">Pattern corpus: score distribution per axis (n={sum(dist["distinctiveness"].values())}), share of rows at each 0-4 score</text>']
    for i, a in enumerate(axes):
        x0 = pad + i * 140
        tot = (sum(dist[a].values()) - dist[a].get("unknown", 0)) or 1
        for sc in range(5):
            frac = dist[a].get(str(sc), 0) / tot
            h = frac * (H - 80)
            x = x0 + sc * (bw - 2)
            s.append(f'<rect x="{x}" y="{H - h:.1f}" width="{bw - 6}" height="{h:.1f}" fill="{shades[sc]}"/>')
            s.append(f'<text x="{x + 2}" y="{H + 14}" font-size="10" fill="{ink}">{sc}</text>')
            if frac >= 0.01:
                s.append(f'<text x="{x}" y="{H - h - 3:.1f}" font-size="9" fill="{ink}">{round(frac*100)}%</text>')
        s.append(f'<text x="{x0}" y="{H + 32}" font-size="12" fill="{ink}">{a}</text>')
    s.append(f'<text x="{pad}" y="{H + 58}" font-size="11" fill="{ink}">Heuristic, no source priors. Taste bars exclude rows with unknown taste (no pixels/no entry craft evidence); see distribution.json.</text>')
    s.append("</svg>")
    path.write_text("\n".join(s))

# Read-through overrides (evidence: judged_sample.md). Applied as final_action; heuristic action kept.
def final_pattern(p):
    return p["action"]  # no row-level overrides after removal of priors; see judged_sample.md

SUPP_OVERRIDES = {("anti_generic_system.json", "spacing_system"): "rewrite",
                  ("anti_generic_system.json", "color_overrides"): "fix-invalid-values",
                  ("component_code.json", "HeroSection"): "cull"}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(p.relative_to(RT) for p in RT.rglob("*.json"))
    mirror = {str(f): (sha(RT / f), sha(MIRROR / f) if (MIRROR / f).exists() else None) for f in files}
    rows = load("patterns.json")
    token_sets = load("tokens/token_sets.json")
    pats = score_patterns(rows, token_sets)
    for p in pats: p["final_action"] = final_pattern(p)
    tu = C.Counter(r.get("semantic_tokens") for r in rows)
    sup = score_supplemental(flatten_supplemental(), {str(k): v for k, v in tu.items()})
    for x in sup: x["final_action"] = SUPP_OVERRIDES.get((x["file"], x["key"]), x["action"])
    for name, data in (("patterns_scored.csv", pats), ("supplemental_scored.csv", sup)):
        with open(OUT / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator="\n"); w.writeheader(); w.writerows(data)
    with open(OUT / "action_list.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["scope", "id_or_key", "source_or_file", "heuristic_action", "final_action", "ad_keep", "reasons",
                                        "runtime_path", "mirror_path"])
        for p in pats:
            w.writerow(["pattern", p["id"], p["source"], p["action"], p["final_action"], p["ad_keep"], p["reasons"],
                        "design_mcp/data/patterns.json", "data/patterns.json"])
        for s in sup:
            w.writerow(["supplemental", s["key"], s["file"], s["action"], s["final_action"], s["ad_keep"], s["tells"],
                        f"design_mcp/data/{s['file']}", f"data/{s['file']}"])
    axes = ["distinctiveness", "taste", "usefulness", "completeness", "ad_keep"]
    dist = {a: {(str(k) if k != "" else "unknown"): v for k, v in sorted(C.Counter(p[a] for p in pats).items(), key=lambda kv: str(kv[0]))} for a in axes}
    summary = {
        "inputs": {"runtime_dir": "design_mcp/data", "mirror_dir": "data", "sha256_runtime_vs_mirror": mirror,
                   "mirror_identical": all(a == b for a, b in mirror.values())},
        "patterns_total": len(pats),
        "distribution": dist,
        "actions": dict(C.Counter(p["action"] for p in pats)),
        "taste_basis": dict(C.Counter(p["taste_basis"] for p in pats)),
        "asset_state": dict(C.Counter(p["asset_state"] for p in pats)),
        "source_prior_vs_action_comparison_only": {str(k): dict(C.Counter(p["action"] for p in pats if p["source_prior_rank_comparison_only"] == k)) for k in (1, 2, 3)},
        "final_actions": dict(C.Counter(p["final_action"] for p in pats)),
        "final_actions_by_source": {s: dict(C.Counter(p["final_action"] for p in pats if p["source"] == s))
                                    for s in sorted({p["source"] for p in pats})},
        "supplemental_final_actions": dict(C.Counter(x["final_action"] for x in sup)),
        "actions_by_source": {s: dict(C.Counter(p["action"] for p in pats if p["source"] == s))
                              for s in sorted({p["source"] for p in pats})},
        "unique_behavioral_descriptions": len({r["behavioral_description"] for r in rows}),
        "junk_named_rows": sum("junk-page-name" in p["reasons"] for p in pats),
        "asset_blob_absent_rows": sum("asset-blob-absent" in p["reasons"] for p in pats),
        "placeholder_layout_rows": sum("placeholder-layout-notes" in p["reasons"] for p in pats),
        "token_set_usage_top": C.Counter(r.get("semantic_tokens") for r in rows).most_common(5),
        "supplemental_total": len(sup),
        "supplemental_actions": dict(C.Counter(s["action"] for s in sup)),
        "supplemental_by_file": {f: dict(C.Counter(s["action"] for s in sup if s["file"] == f))
                                 for f in sorted({s["file"] for s in sup})},
        "supplemental_tell_counts": dict(C.Counter(t for s in sup for t in s["tells"].split("|") if t)),
        "unscored_files_reason": {
            "vision_results.json": "742 raw vision labels already merged into patterns rows (verified by key overlap); scored via patterns",
            "remaining_vision.json": "173 work-queue stubs (id,name,image_url) - build artifact, no content",
            "batch_list.json": "728 work-queue stubs (image_url,path,name) - build artifact, no content"},
    }
    vr = load("vision_results.json")
    pat_imgs = {r.get("image_url") for r in rows} | {r.get("source_url") for r in rows}
    summary["vision_results_keys_matched_in_patterns"] = sum(k in pat_imgs for k in vr)
    (OUT / "distribution.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    svg_chart(dist, OUT / "distribution.svg")
    print(json.dumps({k: summary[k] for k in ("patterns_total", "actions", "actions_by_source",
                                              "supplemental_actions", "junk_named_rows",
                                              "vision_results_keys_matched_in_patterns")}, indent=0))
    print("mirror_identical", summary["inputs"]["mirror_identical"])
    print("dist", json.dumps(dist))

if __name__ == "__main__":
    main()
