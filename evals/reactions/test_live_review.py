import json

import pytest

from live_review import PACKAGE_COMMIT, eligible_pair, generate


@pytest.fixture
def pair(tmp_path):
    case = "dashboard-clear"
    for arm in ("plain", "design-mcp"):
        cell = tmp_path / case / arm
        cell.mkdir(parents=True)
        contents = {"index.html": b"<h1>Load board</h1>", "client.jsonl": b"{}", "prompt.txt": b"calmer"}
        for name, data in contents.items():
            (cell / name).write_bytes(data)
        (cell / "receipt.json").write_text(json.dumps({
            "case": case, "arm": arm, "source_commit": PACKAGE_COMMIT if arm == "design-mcp" else None,
            "client": "codex-cli 0.170.0", "model": "generator", "effort": "max", "reaction_number": 1,
            "thread_id": f"{arm}-session", "status": "passed", "usage": {"input_tokens": 10},
            "html_sha256": generate.sha256(contents["index.html"]),
            "trace_sha256": generate.sha256(contents["client.jsonl"]),
            "prompt_sha256": generate.sha256(contents["prompt.txt"]),
        }))
    return tmp_path, case


def test_matching_pair_serves_the_verified_bytes(pair):
    labeled = eligible_pair(*pair)
    assert set(labeled) == {"A", "B"}
    assert {receipt["arm"] for receipt, _ in labeled.values()} == {"plain", "design-mcp"}
    assert all(html == b"<h1>Load board</h1>" for _, html in labeled.values())


def test_pair_with_a_different_reaction_round_is_ineligible(pair):
    root, case = pair
    receipt_path = root / case / "plain" / "receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["reaction_number"] = 2
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="reaction_number"):
        eligible_pair(*pair)


def test_pair_with_html_changed_after_generation_is_ineligible(pair):
    root, case = pair
    (root / case / "design-mcp" / "index.html").write_text("<h1>Different board</h1>")
    with pytest.raises(ValueError, match="design-mcp/index.html"):
        eligible_pair(*pair)
