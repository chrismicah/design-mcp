"""CLI entry point for design-mcp.

Usage:
    design-mcp serve     Start the MCP server (stdio transport)
    design-mcp version   Show version
"""
import sys


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print("Design Intelligence MCP Server")
        print()
        print("Usage:")
        print("  design-mcp serve      Start the MCP server (stdio transport)")
        print("  design-mcp version    Show version")
        print()
        print("Add to Claude Code:")
        print("  claude mcp add -s user design-mcp -- design-mcp serve")
        return

    command = args[0]

    if command == "version":
        from design_mcp import __version__
        print(f"design-mcp {__version__}")
        return

    if command == "serve":
        from design_mcp.server import mcp
        mcp.run()
        return

    print(f"Unknown command: {command}", file=sys.stderr)
    print("Run 'design-mcp --help' for usage", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
