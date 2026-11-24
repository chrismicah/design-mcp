"""Expose the official UI UX Pro Max CLI to the matched generation benchmark."""

import argparse
from pathlib import Path
import subprocess
import sys

from fastmcp import FastMCP
from mcp.types import ToolAnnotations


PIN = "a38d04c3d5c298c851dbe5e6ee1965ee3de42cb5"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    git = ["git", "-C", str(checkout)]
    observed = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output([*git, "status", "--porcelain"], text=True)
    launcher = checkout / "src/ui-ux-pro-max/scripts/search.py"
    if observed != PIN or status or not launcher.is_file():
        raise SystemExit(f"Use a clean UI UX Pro Max checkout at {PIN}.")

    server = FastMCP("UI UX Pro Max benchmark adapter")

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
    def design_guidance(query: str, design_system: bool = False) -> str:
        """Get UI UX Pro Max guidance for the project's job and audience.

        Use design_system for a full recommended layout, typography, palette, and interaction guidance.
        Otherwise this returns up to three ranked matches from the automatic search domain.
        """
        if not query.strip() or len(query) > 12000:
            raise ValueError("Supply a query of 1–12,000 characters.")
        options = ["--design-system", "--format", "markdown"] if design_system else ["--max-results", "3"]
        response = subprocess.run(
            [sys.executable, "-B", str(launcher), *options, "--", query],
            cwd=checkout, capture_output=True, text=True, check=True, timeout=20,
        )
        return response.stdout

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
