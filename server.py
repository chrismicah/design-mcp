"""Compatibility entry point for historical source-checkout MCP configurations."""

import os
import sys


if __name__ == "__main__":
    from design_mcp.cli import main

    os.environ.setdefault("DESIGN_MCP_SURFACE", "legacy")
    sys.argv[1:1] = ["serve"]
    main()
else:
    from design_mcp import server

    sys.modules[__name__] = server
