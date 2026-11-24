from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import select
import shutil
import subprocess
import tempfile
import time

command = shutil.which("design-mcp")
if not command:
    raise SystemExit("design-mcp must already be installed")
env = {k: os.environ[k] for k in ("HOME", "PATH", "LANG", "TMPDIR") if k in os.environ}
version = subprocess.check_output([command, "version"], env=env, text=True).strip()
with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryFile() as errors:
    server = subprocess.Popen(
        [command, "serve"], cwd=directory, env=env, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=errors, text=True,
    )

    def request(method, params, message_id=None):
        message = dict(jsonrpc="2.0", method=method, params=params)
        if message_id is not None:
            message["id"] = message_id
        server.stdin.write(json.dumps(message) + "\n")
        server.stdin.flush()
        if message_id is None:
            return None
        if not select.select([server.stdout], [], [], 12)[0]:
            raise TimeoutError(method)
        response = json.loads(server.stdout.readline())
        assert response["id"] == message_id, response
        assert "error" not in response, response
        return response["result"]

    try:
        started = time.monotonic()
        hello = request("initialize", {
            "protocolVersion":"2025-06-18", "capabilities":{},
            "clientInfo":{"name":"design-mcp-audit", "version":"1"},
        }, 1)
        elapsed = round(time.monotonic() - started, 3)
        request("notifications/initialized", {})
        tools = request("tools/list", {}, 2)["tools"]
        default = request("tools/call", {"name":"get_semantic_tokens","arguments":{}}, 3)
        custom = request("tools/call", {"name":"get_semantic_tokens","arguments":{"primary_color":"#793C22"}}, 4)
        assert not default.get("isError") and not custom.get("isError")
        record = {
            "utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Existing installed executable from a temporary directory via stdio. No fresh installation.",
            "version_stdout":version,
            "initialize_server_info":hello["serverInfo"],
            "negotiated_protocol":hello["protocolVersion"],
            "initialize_seconds":elapsed,
            "tool_count":len(tools),
            "tool_names":[t["name"] for t in tools],
            "get_semantic_tokens": {
                "requested_custom_color":"#793C22",
                "custom_equals_default":custom == default,
                "default_result_sha256":hashlib.sha256(json.dumps(default, sort_keys=True).encode()).hexdigest(),
            },
        }
    finally:
        server.stdin.close()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.terminate()
            server.wait(timeout=3)

print(json.dumps(record, indent=2))
