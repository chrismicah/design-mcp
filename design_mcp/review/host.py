"""Chrome native-messaging host for the review extension.

Chrome starts this process when the extension sends a capture and passes the calling extension's origin
as an argument. The process serves exactly one bounded request from exactly one allowed origin, replies
once and exits. It opens no port, reads no credentials and writes only inside this tool's own folder.
"""

import json
import re
import shlex
import struct
import sys
from pathlib import Path

from design_mcp import __version__

from .evidence import SCHEMA
from .pipeline import review, state_dir

HOST_NAME = "com.design_mcp.review"
MAX_REQUEST = 24 * 1024 * 1024
MAX_REPLY = 512 * 1024  # Chrome drops replies over 1 MB; a critique is a few kilobytes.
_ORIGIN = re.compile(r"chrome-extension://[a-p]{32}/\Z")
_EXTENSION_ID = re.compile(r"[a-p]{32}\Z")


class FrameError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class InstallError(ValueError):
    pass


def read_frame(stream, limit=MAX_REQUEST):
    """Read one length-prefixed JSON object. The length is checked before any of the body is read."""
    header = stream.read(4)
    if len(header) != 4:
        raise FrameError("no-request", "No capture arrived.")
    (size,) = struct.unpack("=I", header)
    if not 0 < size <= limit:
        raise FrameError("frame-too-large", "The capture is larger than the local reviewer accepts.")
    chunks, remaining = [], size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise FrameError("truncated", "The capture arrived incomplete. Scan the page again.")
        chunks.append(chunk)
        remaining -= len(chunk)
    try:
        message = json.loads(b"".join(chunks).decode("utf-8"))
    except (ValueError, RecursionError):
        raise FrameError("malformed", "The capture could not be read. Scan the page again.") from None
    if not isinstance(message, dict):
        raise FrameError("malformed", "The capture could not be read. Scan the page again.")
    return message


def write_frame(stream, message, limit=MAX_REPLY):
    data = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(data) > limit:
        data = json.dumps(
            {"ok": False, "code": "reply-too-large", "message": "The result was too large to send back."},
            separators=(",", ":"),
        ).encode("utf-8")
    stream.write(struct.pack("=I", len(data)) + data)
    stream.flush()


def handle(message, root=None):
    kind = message.get("type")
    if kind == "ping":
        return {"ok": True, "host": HOST_NAME, "version": __version__, "schema": SCHEMA}
    if kind == "review":
        return review(message.get("bundle"), root)
    return {"ok": False, "code": "unknown-request", "message": "The local reviewer did not understand the request."}


def main(argv=None, stdin=None, stdout=None, root=None):
    """Serve one request. The first two arguments pin the only origin allowed to call."""
    argv = list(sys.argv[1:] if argv is None else argv)
    allowed = argv[1] if len(argv) >= 2 and argv[0] == "--allowed-origin" else None
    callers = [value for value in argv[2:] if not value.startswith("--")]
    if not (allowed and _ORIGIN.match(allowed) and callers[:1] == [allowed]):
        print("design-mcp review host: the caller is not the allowed extension.", file=sys.stderr)
        return 2
    stdin = sys.stdin.buffer if stdin is None else stdin
    stdout = sys.stdout.buffer if stdout is None else stdout
    try:
        reply = handle(read_frame(stdin), root)
    except FrameError as error:
        reply = {"ok": False, "code": error.code, "message": error.message}
    except Exception:  # the process boundary: always answer in the protocol, never with a traceback on stdout
        reply = {"ok": False, "code": "internal", "message": "The local reviewer hit an error. Nothing was saved."}
    write_frame(stdout, reply)
    return 0 if reply.get("ok") else 1


def manifest_dir(home, platform):
    if platform == "darwin":
        return home / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"
    if platform.startswith("linux"):
        return home / ".config" / "google-chrome" / "NativeMessagingHosts"
    raise InstallError("Connecting the extension is set up for Chrome on macOS and Linux in this build.")


def plan_install(extension_id, home=None, python=None, platform=None):
    """The two files `install` writes: a launcher and Chrome's host manifest, both pinned to one extension."""
    if not isinstance(extension_id, str) or not _EXTENSION_ID.match(extension_id):
        raise InstallError(
            "An extension ID is 32 letters from a to p. Copy it from the extension's popup or chrome://extensions."
        )
    home = Path(home) if home is not None else Path.home()
    platform = platform or sys.platform
    origin = f"chrome-extension://{extension_id}/"
    launcher_path = state_dir(home, platform) / "review-host"
    launcher = (
        "#!/bin/sh\n"
        "# Written by `design-mcp review --install-host`. Starts the local reviewer for one extension only.\n"
        f"exec {shlex.quote(str(python or sys.executable))} -I -m design_mcp.review.host "
        f'--allowed-origin {shlex.quote(origin)} "$@"\n'
    )
    manifest = {
        "name": HOST_NAME,
        "description": "Design MCP local page review",
        "path": str(launcher_path),
        "type": "stdio",
        "allowed_origins": [origin],
    }
    return {
        "origin": origin,
        "launcher_path": launcher_path,
        "launcher": launcher,
        "manifest_path": manifest_dir(home, platform) / f"{HOST_NAME}.json",
        "manifest": manifest,
    }


def install(extension_id, home=None, python=None, platform=None):
    plan = plan_install(extension_id, home, python, platform)
    plan["launcher_path"].parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    plan["launcher_path"].write_text(plan["launcher"], encoding="utf-8")
    plan["launcher_path"].chmod(0o700)
    plan["manifest_path"].parent.mkdir(parents=True, exist_ok=True)
    plan["manifest_path"].write_text(json.dumps(plan["manifest"], indent=2) + "\n", encoding="utf-8")
    return plan


def uninstall(home=None, platform=None):
    """Remove only the two files `install` writes. Returns the paths that were removed."""
    home = Path(home) if home is not None else Path.home()
    platform = platform or sys.platform
    removed = []
    for path in (manifest_dir(home, platform) / f"{HOST_NAME}.json", state_dir(home, platform) / "review-host"):
        if path.is_file():
            path.unlink()
            removed.append(path)
    return removed


if __name__ == "__main__":
    sys.exit(main())
