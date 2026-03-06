"""CLI entry point for design-mcp.

Usage:
    design-mcp serve     Start the MCP server (stdio transport)
    design-mcp version   Show version
"""
import sys
import os


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
        # Find server.py relative to this package
        package_dir = os.path.dirname(os.path.abspath(__file__))
        
        # When installed via pip, server.py is at the repo root (one level up from design_mcp/)
        # When installed in editable mode, it's also at the repo root
        repo_root = os.path.dirname(package_dir)
        server_path = os.path.join(repo_root, "server.py")
        
        if not os.path.exists(server_path):
            # Fallback: check if we're in the installed package with bundled server
            server_path = os.path.join(package_dir, "server.py")
        
        if not os.path.exists(server_path):
            print(f"Error: server.py not found at {server_path}", file=sys.stderr)
            print("Make sure you installed with: pip install -e .", file=sys.stderr)
            sys.exit(1)
        
        # Add repo root to path so server.py can find its modules
        sys.path.insert(0, repo_root)
        os.chdir(repo_root)
        
        # Import and run
        import importlib.util
        spec = importlib.util.spec_from_file_location("server", server_path)
        server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server)
        server.mcp.run()
        return
    
    print(f"Unknown command: {command}", file=sys.stderr)
    print("Run 'design-mcp --help' for usage", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
