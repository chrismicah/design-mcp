"""CLI entry point for design-mcp.

Usage:
    design-mcp serve     Start the MCP server (stdio transport)
    design-mcp version   Show version
    design-mcp review    Review a page locally
    design-mcp review-app    Review a local Swift or Electron capture
    design-mcp doctor    Check the installation and local stdio connection
"""
import sys


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print("Design Intelligence MCP Server")
        print()
        print("Usage:")
        print("  design-mcp serve [--review]    Start the MCP server with optional browser review")
        print("  design-mcp version    Show version")
        print("  design-mcp review     Review a page locally (run review --help)")
        print("  design-mcp review-app CAPTURE    Check a local Swift or Electron capture")
        print("  design-mcp doctor [--repair]    Check the interpreter, resources, and local stdio client")
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

        if args[1:] == ["--review"]:
            from design_mcp.server import enable_browser_review

            enable_browser_review()
        elif args[1:]:
            if args[1:] in (["--help"], ["-h"]):
                print("Usage: design-mcp serve [--review]")
                return
            sys.exit("Usage: design-mcp serve [--review]")
        mcp.run()
        return

    if command == "review":
        from design_mcp.review.cli import main as review_main
        sys.exit(review_main(args[1:]))

    if command == "review-app":
        from design_mcp.desktop_review import main as review_app
        sys.exit(review_app(args[1:]))

    if command == "doctor":
        import argparse
        from design_mcp.doctor import run

        parser = argparse.ArgumentParser(prog="design-mcp doctor", description="Check the local installation.")
        parser.add_argument("--repair", action="store_true", help="Rebuild a missing or corrupt legacy cache.")
        sys.exit(run(repair=parser.parse_args(args[1:]).repair))

    print(f"Unknown command: {command}", file=sys.stderr)
    print("Run 'design-mcp --help' for usage", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
