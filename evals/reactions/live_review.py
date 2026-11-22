"""Run an independent Playwriter ballot on a matched reaction-pilot pair."""

import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
from secrets import SystemRandom
import socket
import subprocess
import sys

from benchmark_input import benchmark_cells, load_spec
from pilot import PACKAGE_COMMIT, generate
from render import child, dynamic_port, fixture_server, query_json, wait_ready

HERE = Path(__file__).resolve().parent
DRIVER = HERE.parent / "v1" / "live_browser.py"
TASKS = {
    "dashboard-clear": (
        "You dispatch a morning logistics shift. Use the controls to focus LS-057 at Bay 4, delayed "
        "19 minutes. Verify that five loads appear initially and LS-061 is due in nine minutes. Check "
        "whether that deadline remains readable during focus. Restore all five loads, then verify "
        "where the reversal control appears and where keyboard focus returns."
    ),
    "pricing-misleading": (
        "You are choosing a plan for Relay Notes. Select Team by keyboard and continue after "
        "verifying its $28 monthly price, 40 hours and shared vocabulary. Verify Solo's $12 and 10 hours "
        "and Studio's $60, 120 hours and approvals. Return to the choices and verify where focus lands. "
        "Check whether the allowances are easy to compare and the selected plan is clear. Report any "
        "billing interval that the UI shows and distinguish it from an interval the brief supplies."
    ),
}


def eligible_pair(cells, case):
    pair = []
    for arm in ("plain", "design-mcp"):
        cell = cells / case / arm
        receipt = json.loads((cell / "receipt.json").read_bytes())
        if receipt["status"] != "passed" or not receipt["usage"]:
            raise ValueError(f"Ineligible generation receipt for {case}/{arm}")
        source = PACKAGE_COMMIT if arm == "design-mcp" else None
        if (receipt["case"], receipt["arm"], receipt["source_commit"]) != (case, arm, source):
            raise ValueError(f"Unexpected generation identity for {case}/{arm}")
        html = (cell / "index.html").read_bytes()
        for filename, field, contents in (
            ("index.html", "html_sha256", html),
            ("client.jsonl", "trace_sha256", (cell / "client.jsonl").read_bytes()),
            ("prompt.txt", "prompt_sha256", (cell / "prompt.txt").read_bytes()),
        ):
            if generate.sha256(contents) != receipt[field]:
                raise ValueError(f"Hash mismatch for {case}/{arm}/{filename}")
        pair.append((receipt, html))
    control, candidate = (item[0] for item in pair)
    for field in ("client", "model", "effort", "prompt_sha256", "reaction_number"):
        if control.get(field) != candidate.get(field):
            raise ValueError(f"Unmatched generation field: {field}")
    thread_ids = [item.get("thread_id") for item in (control, candidate)]
    if not all(thread_ids) or len(set(thread_ids)) != 2:
        raise ValueError("The generators must have two distinct recorded sessions")
    SystemRandom().shuffle(pair)
    return dict(zip(("A", "B"), pair, strict=True))


def critic_prompt(case, spec=None):
    labels = tuple("ABC"[:len(spec["arms"])]) if spec else ("A", "B")
    names = " and ".join(labels) if len(labels) == 2 else "A, B, and C"
    screens = ", ".join(f"{label}-{width}" for label in labels for width in (1440, 390))
    task = spec["task"] if spec else TASKS[case]
    choices = ", ".join(labels[:-1]) + f" or {labels[-1]}"
    return f"""Review anonymous views {names} live. Use only the review tools. Open each at 1440 and 390 CSS pixels in a fresh view. Complete one view before opening the next. Choose the keyboard input yourself. Capture initial and resulting states named like A-1440-before and A-1440-after. Then exercise the recovery or edge state.

Task: {task}

Score coherence and originality at 30% each and craft and usability at 20% each on a 0–10 scale. Calibration examples in that order: a working filter with repeated room cards and equal emphasis gets 5, 3, 6, 7. A distinctive listening schedule with reliable task completion and clear focus gets 9.5, 9.5, 9.5, 10. First rate the withheld example: a legible repair intake with clear labels, familiar layout and misplaced focus after an invalid number. Use 9.5+ only when you find no material weakness. Ground your observations in the rendered layout, visible changes and actual behavior. Do not infer the revision history or generator identity.

Return one JSON object in a json code fence. Include calibration (four scores), screens (keys {screens}, each with coherence, originality, craft, usability, primary_action with input/expected/observed, edge_observation, fact_check, strength, weakness and repair) and preference (winner {choices} or tie with reason). Leave untested views unscored. Flag unsupported claims.
"""


def run(args):
    if args.spec:
        inputs = list(benchmark_cells(args.cells, args.spec).values())
        SystemRandom().shuffle(inputs)
        pair = dict(zip("ABC", inputs))
    else:
        pair = eligible_pair(args.cells, args.case)
    version = subprocess.check_output([str(args.playwriter), "--version"], text=True).strip()
    if version != "0.12.0":
        raise ValueError(f"Expected Playwriter 0.12.0, got {version}")
    args.out.mkdir(mode=0o700, parents=True)
    generate.check_quota(args.quota_probe, args.out)
    key = {label: {field: receipt[field] for field in ("arm", "html_sha256", "thread_id")}
           for label, (receipt, _) in pair.items()}
    (args.out / "sealed-key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    if args.spec:
        (args.out / "benchmark-spec.json").write_text(json.dumps(args.spec, indent=2) + "\n", encoding="utf-8")
    prompt = critic_prompt(args.case, args.spec)
    (args.out / "critic-prompt.md").write_text(prompt, encoding="utf-8")

    relay_port = dynamic_port()
    relay_env = {key: value for key, value in generate.clean_env().items() if not key.startswith("PLAYWRITER_")}
    relay_env.update(PLAYWRITER_PORT=str(relay_port), PLAYWRITER_LOG_FILE_PATH=str(args.out / "playwriter.log"))
    profile = args.out / "profile"
    chrome_args = [
        str(args.chrome), "--headless", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
        "--disable-sync", "--disable-background-networking", "--disable-component-update",
        "--disable-features=OptimizationGuideModelDownloading,OptimizationHints", "--disk-cache-size=1048576",
        f"--user-data-dir={profile}", "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0", "about:blank",
    ]
    with ExitStack() as stack:
        chrome = stack.enter_context(child(chrome_args, args.out / "chrome.log"))
        cdp_port = wait_ready(chrome, lambda: int((profile / "DevToolsActivePort").read_text().splitlines()[0]))
        browser = wait_ready(chrome, lambda: query_json(f"http://127.0.0.1:{cdp_port}/json/version"))
        if args.spec and args.spec.get("browser", browser["Browser"]) != browser["Browser"]:
            raise ValueError(f"Benchmark browser differs from its pin: {browser['Browser']}")
        relay_args = [str(args.playwriter), "serve", "--host", "127.0.0.1"]
        relay = stack.enter_context(child(relay_args, args.out / "relay.log", env=relay_env))

        def relay_ready():
            with socket.create_connection(("127.0.0.1", relay_port), timeout=1):
                return True

        wait_ready(relay, relay_ready)
        pages = {}
        for label, (_, fixture) in pair.items():
            server = stack.enter_context(fixture_server())
            server.fixture = fixture
            pages[label] = f"http://127.0.0.1:{server.server_port}/index.html"
        config = {
            "playwriter": str(args.playwriter), "relay_port": relay_port, "cdp": browser["webSocketDebuggerUrl"],
            "pages": pages, "evidence_dir": str(args.out / "captures"), "original_capture": True,
        }
        config_path = args.out / "driver-config.json"
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        (args.out / "browser-version.txt").write_text(browser["Browser"] + "\n", encoding="utf-8")
        table = generate.mcp_table(sys.executable, "review", ["-B", str(DRIVER), "--config", str(config_path)],
                                   {}, ("open_view", "act", "capture"))
        command = generate.client_command(args, table)
        with (args.out / "critic.jsonl").open("w") as stdout, (args.out / "critic.stderr").open("w") as stderr:
            return subprocess.run(command, input=prompt, text=True, cwd=args.out, env=generate.clean_env(),
                                  stdout=stdout, stderr=stderr, timeout=720).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    absolute_path = lambda value: Path(value).expanduser().absolute()
    parser.add_argument("--cells", required=True, type=absolute_path)
    for option in ("out", "playwriter", "chrome", "quota-probe"):
        parser.add_argument(f"--{option}", type=absolute_path)
    study = parser.add_mutually_exclusive_group(required=True)
    study.add_argument("--case", choices=tuple(TASKS))
    study.add_argument("--benchmark-spec", type=absolute_path)
    parser.add_argument("--check-input", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--effort", default="max")
    args = parser.parse_args()
    args.spec = load_spec(args.benchmark_spec) if args.benchmark_spec else None
    if args.check_input:
        cells = benchmark_cells(args.cells, args.spec) if args.spec else eligible_pair(args.cells, args.case)
        print(json.dumps({"verified_arms": sorted(receipt["arm"] for receipt, _ in cells.values())}))
        return
    if not all((args.out, args.playwriter, args.chrome, args.quota_probe, args.model)):
        parser.error("Live review requires --out, --playwriter, --chrome, --quota-probe and --model")
    args.no_shell = True
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
