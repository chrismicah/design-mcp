#!/usr/bin/env python3
"""Run Design MCP with the trial directions added to its normal library."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from design_mcp import directions
from design_mcp.cli import main
from design_mcp.direction_records import Direction, library


def trial_library():
    records = library()
    candidates = [Direction.model_validate(row) for row in json.loads((HERE / "directions.json").read_text())]
    additions = {candidate.id: candidate for candidate in candidates}
    if len(additions) != len(candidates) or records.keys() & additions.keys():
        raise ValueError("The trial requires unique direction IDs")
    return records | additions


if __name__ == "__main__":
    records = trial_library()
    directions.library = lambda: records
    main()
