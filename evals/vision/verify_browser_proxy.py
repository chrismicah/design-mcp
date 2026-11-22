"""Verify the installed review browser cannot reach an owned private fixture."""

import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

from design_mcp.review import isolated, network


async def verify(chrome, output):
    contacts = []
    attempted = []
    fixture_name = "private-fixture.example"
    marker = b"design-mcp-owned-private-fixture"

    async def local_page(reader, writer):
        contacts.append(True)
        try:
            await reader.read(1024)
            writer.write(b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n" + marker)
            await writer.drain()
        finally:
            writer.close()

    def resolve(host, port, type):
        if host != fixture_name:
            raise socket.gaierror("Only the owned fixture has a test DNS record")
        return [(socket.AF_INET, type, 6, "", ("127.0.0.1", port))]

    guard = network.resolve_public_host

    def observe(host, port, resolver):
        attempted.append((host, port))
        return guard(host, port, resolver)

    fixture = await asyncio.start_server(local_page, "127.0.0.1", 0)
    async with fixture:
        port = fixture.sockets[0].getsockname()[1]
        with tempfile.TemporaryDirectory() as parent, patch.object(network, "resolve_public_host", observe):
            async with network.public_proxy("public.example", "93.184.216.34", resolve) as proxy_port:
                for index, host in enumerate(("127.0.0.1", fixture_name)):
                    args = isolated._browser_arguments(chrome, Path(parent) / f"profile-{index}", proxy_port)
                    process = await asyncio.create_subprocess_exec(
                        *args, "--dump-dom", f"http://{host}:{port}",
                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    )
                    try:
                        stdout, stderr = await asyncio.wait_for(process.communicate(), 30)
                    finally:
                        if process.returncode is None:
                            process.kill()
                            await process.wait()
                    assert (host, port) in attempted, stderr[-600:]
                    assert marker not in stdout and not contacts, "Browser reached the owned loopback fixture"
    output.write_text(json.dumps({
        "proxied_private_targets": ["IPv4 loopback", "test DNS name resolving to loopback"],
        "fixture_connections": len(contacts),
    }, indent=2) + "\n")


if __name__ == "__main__":
    asyncio.run(verify(sys.argv[1], Path(sys.argv[2])))
