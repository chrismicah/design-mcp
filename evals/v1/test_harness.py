"""Check receipt parsing and paired scoring without a provider or browser."""

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from generate import parse_cell, sha256
from judge import WIDTHS, create_pair, summarize, write


class BenchmarkTests(unittest.TestCase):
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
            args = SimpleNamespace(cells=base / "generated", out=base / "blind", seed="test")
            task = {"id": "station"}
            for arm in ("none", "v2"):
                cell = args.cells / task["id"] / arm
                cell.mkdir(parents=True)
                html = b"<body>Test</body>"
                (cell / "index.html").write_bytes(html)
                write(cell / "receipt.json", {"status": "passed", "html_sha256": sha256(html)})
                captures = {}
                for width in WIDTHS:
                    image = f"fixture:{arm}:{width}".encode()
                    (cell / f"{width}.png").write_bytes(image)
                    captures[width] = {
                        "status": "rendered", "sha256": sha256(image), "viewport": int(width),
                        "width": int(width), "language": "en", "pageErrors": [], "accessibility": "",
                    }
                write(cell / "render.json", {"input_sha256": sha256(html), "captures": captures})

            blind, labels, _ = create_pair(args, task)
            self.assertEqual(set(labels.values()), {"none", "v2"})
            self.assertEqual((blind / "A-390.png").read_bytes(), f"fixture:{labels['A']}:390".encode())
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


if __name__ == "__main__":
    unittest.main()
