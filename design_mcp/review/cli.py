"""`design-mcp review`: the local side of the page review. Standard library only, so it starts fast."""

import argparse
import json
import re
import sys
import time
import webbrowser
from pathlib import Path

from .address import credentials_reason, local_address_reason
from .evidence import EvidenceError, inspect_url
from .pipeline import _ms, describe, review

EXTENSION_DIR = Path(__file__).with_name("extension")
_HAS_SCHEME = re.compile(r"^(?:[a-z][a-z0-9+.-]*://|(?:about|blob|chrome|data|file|javascript|mailto|view-source):)", re.I)


def _parser():
    parser = argparse.ArgumentParser(
        prog="design-mcp review",
        description="Find the first thing to fix on a web page and preview the change. "
                    "Everything runs on this computer.",
    )
    parser.add_argument("url", nargs="?", help="a public page to open in your browser for a scan")
    parser.add_argument("--evidence", metavar="FILE", help="review a saved capture instead of a live page")
    parser.add_argument("--out", metavar="DIR",
                        help="folder for the preview (default: a private folder in your user directory)")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    parser.add_argument("--no-open", action="store_true", help="say what would open without opening a browser")
    parser.add_argument("--playwriter", nargs="?", const="", metavar="PATH",
                        help="capture the URL in a separate, cookie-free Chrome using Playwriter on PATH")
    parser.add_argument("--chrome", metavar="PATH", help="Chrome executable to use with --playwriter")
    parser.add_argument("--extension-path", action="store_true",
                        help="print the folder to load in chrome://extensions")
    parser.add_argument("--install-host", metavar="EXTENSION_ID",
                        help="let the extension with this ID start the local reviewer")
    parser.add_argument("--uninstall-host", action="store_true", help="remove what --install-host wrote")
    parser.add_argument("--chrome-user-data-dir", metavar="DIR",
                        help="use this Chrome data directory for the host and its saved reviews")
    parser.add_argument("--dry-run", action="store_true", help="with --install-host, show the files without writing")
    return parser


def _report(result, as_json):
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n".join(describe(result)), file=sys.stdout if result["ok"] else sys.stderr)
    return 0 if result["ok"] else 1


def _host_setup(args):
    from . import host

    try:
        options = {"chrome_user_data_dir": args.chrome_user_data_dir}
        if args.uninstall_host:
            removed = host.uninstall(**options)
            print("\n".join(f"Removed {path}" for path in removed) or "Nothing to remove.")
            return 0
        configure = host.plan_install if args.dry_run else host.install
        plan = configure(args.install_host, **options)
    except (host.InstallError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    verb = "Would write" if args.dry_run else "Wrote"
    print(f"{verb} {plan['manifest_path']}")
    print(f"{verb} {plan['launcher_path']}")
    print(f"Only {plan['origin']} can start the local reviewer.")
    if not args.dry_run:
        print("Back in Chrome, press “Review this page” again.")
    return 0


def _review_file(args):
    try:
        with open(args.evidence, encoding="utf-8") as stream:
            bundle = json.load(stream)
    except (OSError, ValueError) as error:
        print(f"Could not read {args.evidence}: {error}", file=sys.stderr)
        return 1
    return _report(review(bundle, args.out), args.json)


def _review_url(args, opener):
    started = time.perf_counter()
    pasted = args.url.strip()
    if not _HAS_SCHEME.match(pasted):
        pasted = "https://" + pasted
    try:
        clean, removed = inspect_url(pasted)
    except EvidenceError as error:
        print(error.message, file=sys.stderr)
        return 1
    if removed:
        print(credentials_reason(removed), file=sys.stderr)
        return 1
    reason = local_address_reason(clean)
    if reason:
        print(reason, file=sys.stderr)
        return 1

    if args.playwriter is not None:
        if args.no_open:
            print(f"Would capture {clean} in a separate browser.")
            return 0
        from .isolated import CaptureError, capture

        try:
            bundle = capture(clean, args.playwriter or None, args.chrome)
        except (CaptureError, EvidenceError) as error:
            print(error.message, file=sys.stderr)
            return 1
        review_started = time.perf_counter()
        result = review(bundle, args.out)
        if args.json and result["ok"]:
            before_review = _ms(started, review_started)
            stages = result["timings_ms"]
            result["url_capture_ms"] = {
                **bundle["url_capture_ms"],
                "local_decision": round(before_review + stages["sanitize"] + stages["local_checks"], 1),
                "preview_written": _ms(started, time.perf_counter()),
            }
        return _report(result, args.json)

    print(f"{'Would open' if args.no_open else 'Opening'} {clean} in your browser.")
    print("On that tab in Chrome, click the Design MCP button, then “Review this page”.")
    print("No button yet? Run: design-mcp review --extension-path")
    print("To scan without the extension, add --playwriter after the address. This uses a separate, "
          "cookie-free Chrome.")
    if not args.no_open:
        opener(clean)
    return 0


def main(argv=None, opener=webbrowser.open):
    parser = _parser()
    args = parser.parse_args(argv)
    if args.chrome_user_data_dir is not None and not (args.install_host or args.uninstall_host):
        parser.error("--chrome-user-data-dir requires --install-host or --uninstall-host")
    if args.extension_path:
        print(EXTENSION_DIR)
        print("In Chrome: open chrome://extensions, turn on Developer mode, choose “Load unpacked” "
              "and pick this folder.")
        return 0
    if args.install_host or args.uninstall_host:
        return _host_setup(args)
    if args.evidence:
        return _review_file(args)
    if args.url:
        return _review_url(args, opener)
    parser.print_help()
    return 2
