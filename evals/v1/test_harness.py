"""Check receipt parsing and paired scoring without a provider or browser."""

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from generate import PROMPT, hosted_mcp_table, mcp_table, parse_cell, sha256
from judge import WIDTHS, create_pair, load, summarize, write
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
            (blind / "A-390.png").write_bytes(b"stale staged image")
            with self.assertRaisesRegex(ValueError, "Previously staged blind image differs"):
                create_pair(args, task)
            receipt_path = cell / "receipt.json"
            receipt = load(receipt_path)
            write(receipt_path, {**receipt, "model": "wrong-model"})
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

    def test_competitor_requires_its_own_successful_search(self):
        call = {"type": "item.completed", "item": {"type": "mcp_tool_call", "server": "inspo",
                  "tool": "search_screens", "status": "completed"}}
        turn = {"type": "turn.completed", "usage": {"output_tokens": 7}}
        message = {"type": "item.completed", "item": {
            "type": "agent_message", "text": "```html\n<body>Test</body>\n```"}}
        result, _ = parse_cell([call, message, turn], True, "inspo", "search_screens")
        self.assertTrue(result["treatment_call"])
        self.assertEqual(result["status"], "passed")
        result, _ = parse_cell([call, message, turn], True)
        self.assertEqual(result["status"], "mcp-unused-or-failed")
        config = mcp_table("/test fixtures/start", "inspo", ["--stdio"], {"MODE": "local"})
        self.assertIn('command="/test fixtures/start"', config)
        self.assertIn('env={"MODE"="local"}', config)

    def test_hosted_comparator_accepts_public_https_without_credentials(self):
        config = hosted_mcp_table("https://example.com/mcp?images=none", "hosted")
        self.assertEqual(config, 'mcp_servers={"hosted"={url="https://example.com/mcp?images=none",'
                                 'required=true,default_tools_approval_mode="writes"}}')
        for url in ("http://example.com/mcp", "https://user:password@example.com/mcp", "https://example.com/#secret"):
            with self.assertRaisesRegex(ValueError, "public HTTPS"):
                hosted_mcp_table(url, "hosted")


if __name__ == "__main__":
    unittest.main()
