"""Check receipt parsing and paired scoring without a provider or browser."""

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from audit_scoreboard import matching_run
from generate import PROMPT, hosted_mcp_table, loopback_mcp_table, mcp_table, parse_cell, sha256
from judge import WIDTHS, create_pair, load, run_judge, summarize, write
from probe_competitors import decode_results, ranked_identifiers


class BenchmarkTests(unittest.TestCase):
    def test_competitor_probes_distinguish_ranked_rows_from_empty_results(self):
        def text_reply(*blocks):
            return SimpleNamespace(structured_content=None,
                                   content=[SimpleNamespace(type="text", text=text) for text in blocks])

        reply = SimpleNamespace(structured_content={"results": [{"id": "layout", "asset": "ignored"}]}, content=[])
        self.assertEqual(ranked_identifiers(decode_results(reply, "results")), [{"id": "layout"}])
        self.assertEqual(decode_results(text_reply('{"products": [{"name": "Station"}]}'), "products"),
                         [{"name": "Station"}])
        self.assertEqual(decode_results(text_reply('{"id": "a"}', '{"id": "b"}'), "results"),
                         [{"id": "a"}, {"id": "b"}])
        self.assertEqual(decode_results(text_reply("No results. Try other keywords."), "products"), [])
        self.assertEqual(decode_results(text_reply(), "results"), [])
        with self.assertRaisesRegex(ValueError, "unrecognized"):
            decode_results(text_reply("Unexpected backend response"), "results")

    def test_mcp_use_is_required_only_in_the_treatment(self):
        message = {"type": "item.completed", "item": {
            "type": "agent_message", "text": "```html\n<body>Test</body>\n```"}}
        turn = {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 14}}
        direct = {"type": "item.completed", "item": {
            "type": "mcp_tool_call", "server": "design-mcp", "tool": "direct", "status": "completed"}}

        self.assertEqual(parse_cell([message, turn], False)[0]["status"], "passed")
        self.assertEqual(parse_cell([message, turn], True)[0]["status"], "mcp-unused-or-failed")
        self.assertEqual(parse_cell([direct, message, turn], False)[0]["status"], "control-tool-leak")
        result, html = parse_cell([direct, message, turn], True)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["usage"], turn["usage"])
        self.assertEqual(html, "<body>Test</body>\n")

    def test_candidate_gate_requires_one_completed_reply_with_the_expected_direction(self):
        def reply(direction):
            return {"type": "item.completed", "item": {
                "type": "mcp_tool_call", "server": "design-mcp", "tool": "direct", "status": "completed",
                "result": {"structured_content": {"direction": {"id": direction}}}}}

        message = {"type": "item.completed", "item": {
            "type": "agent_message", "text": "```html\n<body>Test</body>\n```"}}
        turn = {"type": "turn.completed", "usage": {"output_tokens": 10}}
        expected = "search-recovery"
        for directions, status in (
            ([expected], "passed"),
            (["object-hero"], "unexpected-design-direction"),
            ([None], "unexpected-design-direction"),
            (["object-hero", expected], "unexpected-design-direction"),
            ([], "mcp-unused-or-failed"),
        ):
            with self.subTest(directions=directions):
                events = [*(reply(direction) for direction in directions), message, turn]
                result, html = parse_cell(events, True, expected_direction=expected)
                self.assertEqual(result["status"], status)
                self.assertEqual(result["observed_directions"], directions)
                self.assertEqual(html, "<body>Test</body>\n")
        failed = reply(None)
        failed["item"]["status"] = "failed"
        retry, _ = parse_cell([failed, reply(expected), message, turn], True, expected_direction=expected)
        self.assertEqual(retry["status"], "unexpected-design-direction")
        self.assertEqual(retry["observed_directions"], [None, expected])
        historical, _ = parse_cell([reply("object-hero"), message, turn], True)
        self.assertEqual(historical["status"], "passed")
        self.assertNotIn("observed_directions", historical)

    def test_blind_pair_requires_two_intact_renderings(self):
        with TemporaryDirectory() as path:
            base = Path(path)
            args = SimpleNamespace(cells=base / "generated", out=base / "blind", seed="test",
                                   control="none", treatment="v2", compact=False)
            task = {"id": "station", "brief": "Board the train."}
            for arm in ("none", "v2"):
                cell = args.cells / task["id"] / arm
                cell.mkdir(parents=True)
                html = b"<body>Test</body>"
                (cell / "index.html").write_bytes(html)
                write(cell / "receipt.json", {
                    "status": "passed", "case": task["id"], "arm": arm, "model": "fixture-model", "effort": "max",
                    "client": "fixture-client", "prompt_sha256": sha256(PROMPT.format(brief=task["brief"]).encode()),
                    "html_sha256": sha256(html),
                })
                captures = {}
                for width in WIDTHS:
                    image = f"fixture:{arm}:{width}".encode()
                    (cell / f"{width}.png").write_bytes(image)
                    captures[width] = {
                        "status": "rendered", "sha256": sha256(image), "viewport": int(width),
                        "width": int(width), "language": "en", "pageErrors": [], "accessibility": "",
                        "regions": [{"role": "h1", "box": [8, 8, 90, 24]}],
                    }
                (cell / "720.png").write_bytes(f"compact:{arm}".encode())
                write(cell / "render.json", {"input_sha256": sha256(html), "captures": captures,
                                             "browser": "fixture-browser", "renderer": "fixture-renderer"})

            blind, labels, _ = create_pair(args, task)
            self.assertEqual(set(labels.values()), {"none", "v2"})
            self.assertEqual((blind / "A-390.png").read_bytes(), f"fixture:{labels['A']}:390".encode())
            args.model, args.effort = "fixture-judge", "max"
            with self.assertRaisesRegex(ValueError, "No saved ballot"):
                run_judge(args, task, create_pair(args, task), None)
            (blind / "A-390.png").write_bytes(b"stale staged image")
            with self.assertRaisesRegex(ValueError, "Previously staged blind image differs"):
                create_pair(args, task)
            receipt_path = cell / "receipt.json"
            receipt = load(receipt_path)
            write(receipt_path, {**receipt, "model": "wrong-model"})
            with self.assertRaisesRegex(ValueError, "Generator or browser configuration differs"):
                create_pair(args, task)
            write(receipt_path, {**receipt, "shell_tool": False})
            with self.assertRaisesRegex(ValueError, "Generator or browser configuration differs"):
                create_pair(args, task)
            write(receipt_path, {**receipt, "prompt_sha256": "wrong-prompt"})
            with self.assertRaisesRegex(ValueError, "Generation receipt does not match"):
                create_pair(args, task)
            write(receipt_path, receipt)
            args.compact = True
            args.out = base / "blind-compact"
            blind = args.out / task["id"]
            _, _, metrics = create_pair(args, task)
            self.assertEqual((blind / "A-1440.png").read_bytes(), f"compact:{labels['A']}".encode())
            self.assertEqual(metrics["A"][0]["regions"][0]["role"], "h1")
            (cell / "390.png").write_bytes(b"wrong image")
            with self.assertRaisesRegex(ValueError, "Screenshot artifact changed"):
                create_pair(args, task)

    def test_aggregate_reports_coverage_and_ties(self):
        rows = [{"scores": {"none": 50, "v2": 75}}, {"scores": {"none": 70, "v2": 70}}]
        result = summarize([{}, {}, {}], rows)
        self.assertEqual(result["judged_pairs"], 2)
        self.assertEqual(result["requested_pairs"], 3)
        self.assertEqual(result["difference"], 12.5)
        self.assertEqual(result["wins_ties_losses"], [1, 1, 0])
        candidate = summarize([{}], [{"scores": {"v2": 70, "candidate": 80}}], "candidate", "v2")
        self.assertEqual(candidate["difference"], 10)

    def test_scoreboard_requires_one_matching_hosted_archive(self):
        with TemporaryDirectory() as path:
            base = Path(path)
            archives = base / "archives"
            cells = base / "cells"
            correct = archives / "42"
            wrong = archives / "43"
            for root in (correct, wrong, cells):
                for arm in ("none", "v2"):
                    case = root / "station" / arm
                    case.mkdir(parents=True)
                    write(case / "receipt.json", {"arm": arm, "html_sha256": arm})
                    write(case / "render.json", {"input_sha256": "other" if root == wrong else arm})
            self.assertEqual(matching_run(archives, "station", cells), correct)
            with self.assertRaisesRegex(ValueError, "found 0"):
                matching_run(archives, "missing", cells)
            for arm in ("none", "v2"):
                write(wrong / "station" / arm / "render.json", {"input_sha256": arm})
            with self.assertRaisesRegex(ValueError, "found 2"):
                matching_run(archives, "station", cells)

    def test_competitor_requires_its_own_successful_search(self):
        call = {"type": "item.completed", "item": {"type": "mcp_tool_call", "server": "inspo",
                  "tool": "search_screens", "status": "completed"}}
        turn = {"type": "turn.completed", "usage": {"output_tokens": 7}}
        message = {"type": "item.completed", "item": {
            "type": "agent_message", "text": "```html\n<body>Test</body>\n```"}}
        result, _ = parse_cell([call, message, turn], True, "inspo", "search_screens")
        self.assertTrue(result["treatment_call"])
        self.assertEqual(result["status"], "passed")
        recommendation = {"type": "item.completed", "item": {**call["item"], "tool": "recommend"}}
        result, _ = parse_cell([recommendation, message, turn], True, "inspo", ("recommend", "search_screens"))
        self.assertEqual(result["status"], "passed")
        result, _ = parse_cell([recommendation, message, turn], True, "inspo", "search_screens")
        self.assertEqual(result["status"], "mcp-unused-or-failed")
        result, _ = parse_cell([call, message, turn], True)
        self.assertEqual(result["status"], "mcp-unused-or-failed")
        config = mcp_table("/test fixtures/start", "inspo", ["--stdio"], {"MODE": "local"})
        self.assertIn('command="/test fixtures/start"', config)
        self.assertIn('env={"MODE"="local"}', config)
        self.assertIn('default_tools_approval_mode="writes"', config)
        self.assertNotIn('enabled_tools=', config)
        reviewed = mcp_table("/test fixtures/start", "screenshots", [], {}, ["search_inspiration"])
        self.assertIn('enabled_tools=["search_inspiration"],default_tools_approval_mode="approve"', reviewed)

    def test_hosted_comparator_accepts_public_https_without_credentials(self):
        config = hosted_mcp_table("https://example.com/mcp?images=none", "hosted")
        self.assertEqual(config, 'mcp_servers={"hosted"={url="https://example.com/mcp?images=none",'
                                 'required=true,default_tools_approval_mode="writes"}}')
        for url in ("http://example.com/mcp", "https://user:password@example.com/mcp", "https://example.com/#secret"):
            with self.assertRaisesRegex(ValueError, "public HTTPS"):
                hosted_mcp_table(url, "hosted")

    def test_loopback_comparator_restricts_the_http_endpoint_and_tools(self):
        config = loopback_mcp_table("http://127.0.0.1:6006/mcp", "storybook", ["docs-list", "docs-show"])
        self.assertEqual(config, 'mcp_servers={"storybook"={url="http://127.0.0.1:6006/mcp",'
                                 'required=true,enabled_tools=["docs-list", "docs-show"],'
                                 'default_tools_approval_mode="approve"}}')
        for url, tools in (
            ("http://127.0.0.1:6006/mcp", []),
            ("http://localhost:6006/mcp", ["docs-show"]),
            ("http://127.0.0.1:6006@remote.test/mcp", ["docs-show"]),
            ("https://127.0.0.1:6006/mcp", ["docs-show"]),
            ("http://127.0.0.1:65536/mcp", ["docs-show"]),
            ("http://127.0.0.1:6006/mcp?token=test", ["docs-show"]),
        ):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "loopback"):
                loopback_mcp_table(url, "storybook", tools)

    def test_storybook_gallery_requires_the_archived_component_or_story_response(self):
        import json

        folder = Path(__file__).resolve().parent
        fixture = json.loads((folder.parents[1] / "evidence/benchmark-v1/storybook-mcp-probe.json").read_text())
        calls = fixture["verified_attempt"]["calls"]
        config = json.loads((folder / "storybook-gallery.json").read_text())
        hashes = config["required_response_text_sha256"]
        message = {"type": "item.completed", "item": {
            "type": "agent_message", "text": "```html\n<body>Test</body>\n```"}}
        turn = {"type": "turn.completed", "usage": {"output_tokens": 7}}

        def call(label, text=None, **extra_result):
            observed = calls[label]
            return {"type": "item.completed", "item": {
                "type": "mcp_tool_call", "server": "storybook", "tool": observed["tool"], "status": "completed",
                "arguments": observed["arguments"],
                "result": {"content": [{"type": "text", "text": observed["text"] if text is None else text}],
                           "isError": observed["is_error"], **extra_result},
            }}

        for event, status, matched in (
            (call("component"), "passed", ["docs-show"]),
            (call("story"), "passed", ["docs-show-story"]),
            (call("catalog"), "mcp-unused-or-failed", []),
            (call("missing-story"), "required-mcp-response-missing", []),
            (call("component", text="maintenance-disclosure"), "required-mcp-response-missing", []),
            (call("component", isError=True), "required-mcp-response-missing", []),
        ):
            with self.subTest(event=event["item"]["tool"], status=status):
                result, html = parse_cell([event, message, turn], True, "storybook", config["expected_tools"],
                                          required_response_text_sha256=hashes)
                self.assertEqual(result["status"], status)
                self.assertEqual(result["matched_response_tools"], matched)
                self.assertEqual(html, "<body>Test</body>\n")

    def test_shadcn_gate_requires_a_relevant_registry_result(self):
        search = "search_items_in_registries"
        view = "view_items_in_registries"
        examples = "get_item_examples_from_registries"
        found = 'Found 1 items matching "field" in registries @shadcn:\n\nShowing items 1-1 of 1:\n\n'
        field = found + "- field (registry:ui) [@shadcn]"
        unavailable = 'No items found matching "field" in registries @shadcn'
        message = {"type": "item.completed", "item": {
            "type": "agent_message", "text": "```html\n<body>Test</body>\n```"}}
        turn = {"type": "turn.completed", "usage": {"output_tokens": 7}}

        def call(tool, body, status="completed", server="shadcn", arguments=None, **extra_result):
            return {"type": "item.completed", "item": {
                "type": "mcp_tool_call", "server": server, "tool": tool, "status": status, "arguments": arguments,
                "result": {"content": [{"type": "text", "text": body}], **extra_result}}}

        for label, calls, expected, items in (
            ("named search", [call(search, field)], "passed", ["field"]),
            ("named view", [call(view, "Item Details:\n\n## input\n**Type:** registry:ui",
                                 arguments={"items": ["@shadcn/input"]})],
             "passed", ["input"]),
            ("example with code", [call(examples, "# Usage Examples\n\nFound 1 example:\n\n"
                                        "## Example: field-demo\n### Code (field.tsx):\n```tsx\nimport React\n```")],
             "passed", ["field-demo"]),
            ("empty then relevant", [call(search, unavailable), call(search, field)], "passed", ["field"]),
            ("empty", [call(search, unavailable)], "shadcn-relevant-item-missing", []),
            ("query only", [call(search, found + "- accordion (registry:ui) [@shadcn]")],
             "shadcn-relevant-item-missing", []),
            ("other registry", [call(search, found + "- field (registry:ui) [@other]")],
             "shadcn-relevant-item-missing", []),
            ("other registry view", [call(view, "Item Details:\n\n## input\n**Type:** registry:ui",
                                          arguments={"items": ["@other/input"]})],
             "shadcn-relevant-item-missing", []),
            ("no example code", [call(examples, "# Usage Examples\n\n## Example: field-demo")],
             "shadcn-relevant-item-missing", []),
            ("blank example code", [call(examples, "# Usage Examples\n\n## Example: field-demo\n```tsx\n\n```")],
             "shadcn-relevant-item-missing", []),
            ("malformed result", [call(search, field, content=None)], "shadcn-relevant-item-missing", []),
            ("tool result error", [call(search, field, isError=True)], "shadcn-relevant-item-missing", []),
            ("failed", [call(search, field, status="failed")], "mcp-unused-or-failed", []),
            ("wrong server", [call(search, field, server="other")], "mcp-unused-or-failed", []),
        ):
            with self.subTest(label=label):
                result, html = parse_cell([*calls, message, turn], True, "shadcn", (search, view, examples),
                                          required_shadcn_items=("field", "input", "field-demo"))
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["matched_shadcn_items"], items)
                self.assertEqual(html, "<body>Test</body>\n")

    def test_render_preflight_skips_failed_and_unverified_drafts(self):
        from render import eligible_templates

        with TemporaryDirectory() as path:
            root = Path(path)
            html = b"<body>Test</body>"
            for arm, status in (("v2", "passed"), ("shadcn", "shadcn-relevant-item-missing"),
                                ("storybook", "required-mcp-response-missing"),
                                ("router", "unexpected-design-direction"), ("missing", None),
                                ("rendered", "passed")):
                cell = root / "maintenance" / arm
                cell.mkdir(parents=True)
                (cell / "index.html").write_bytes(html)
                if status:
                    write(cell / "receipt.json", {"status": status, "html_sha256": sha256(html)})
                if arm == "rendered":
                    write(cell / "render.json", {})

            eligible = root / "maintenance/v2/index.html"
            self.assertEqual(list(eligible_templates(root, ["maintenance"])), [(eligible, html)])
            self.assertEqual(list(eligible_templates(root, ["unknown"])), [])
            eligible.write_bytes(b"<body>Changed</body>")
            with self.assertRaisesRegex(ValueError, "Generation artifact changed"):
                list(eligible_templates(root))


if __name__ == "__main__":
    unittest.main()
