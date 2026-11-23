"""Loopback-only SOCKS connection gate for the disposable review browser."""

import asyncio
from asyncio import open_connection
from contextlib import asynccontextmanager
import ipaddress
import re
import socket

from .address import canonical_host, is_public_ip, resolve_public_host

_REPLY = b"\x05%s\x00\x01\x00\x00\x00\x00\x00\x00"
_CONNECT_TIMEOUT = 8
_MAX_CONNECTIONS = 64


async def _target(reader, writer):
    version, count = await reader.readexactly(2)
    if version != 5 or not count:
        raise ValueError("Invalid browser proxy greeting")
    if b"\x00" not in await reader.readexactly(count):
        writer.write(b"\x05\xff")
        await writer.drain()
        raise ValueError("Unsupported browser proxy authentication")
    writer.write(b"\x05\x00")
    await writer.drain()
    version, command, reserved, kind = await reader.readexactly(4)
    if (version, command, reserved) != (5, 1, 0):
        raise ValueError("Expected a TCP connection request")
    if kind == 3:
        (length,) = await reader.readexactly(1)
        host = (await reader.readexactly(length)).decode("ascii")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if not re.fullmatch(r"[a-zA-Z0-9_.-]+", host):
                raise ValueError("Invalid browser proxy hostname") from None
    else:
        size = {1: 4, 4: 16}.get(kind)
        if size is None:
            raise ValueError("Invalid browser proxy address type")
        host = str(ipaddress.ip_address(await reader.readexactly(size)))
    port = int.from_bytes(await reader.readexactly(2), "big")
    if not port:
        raise ValueError("Invalid browser proxy port")
    return host, port


async def _copy(reader, writer):
    while chunk := await reader.read(65536):
        writer.write(chunk)
        await writer.drain()
    writer.write_eof()


async def _forward(reader, writer, pinned_host, pinned_address, resolve):
    upstream = None
    copies = ()
    port = None
    try:
        host, port = await asyncio.wait_for(_target(reader, writer), _CONNECT_TIMEOUT)
        if canonical_host(host) == pinned_host:
            address = pinned_address
        else:
            address = await asyncio.wait_for(asyncio.to_thread(resolve_public_host, host, port, resolve),
                                             _CONNECT_TIMEOUT)
        source, upstream = await asyncio.wait_for(open_connection(address, port, flags=socket.AI_NUMERICHOST),
                                                  _CONNECT_TIMEOUT)
        writer.write(_REPLY % b"\x00")
        await writer.drain()
        copies = [asyncio.create_task(_copy(reader, upstream)), asyncio.create_task(_copy(source, writer))]
        await asyncio.gather(*copies)
    except (asyncio.IncompleteReadError, asyncio.TimeoutError, OSError, ValueError):
        if port and not writer.is_closing() and upstream is None:
            writer.write(_REPLY % b"\x02")
    finally:
        for copy in copies:
            copy.cancel()
        if upstream is not None:
            upstream.close()
        writer.close()
        if copies:
            await asyncio.gather(*copies, return_exceptions=True)


@asynccontextmanager
async def public_proxy(host, address, resolve):
    """Serve the browser's TCP requests using only validated numeric destinations."""
    if not is_public_ip(ipaddress.ip_address(address)):
        raise ValueError("The browser needs a public initial address")
    active = {}
    closing = False
    pinned_host = canonical_host(host)

    def accept(reader, writer):
        if closing or len(active) >= _MAX_CONNECTIONS:
            writer.close()
            return
        task = asyncio.create_task(_forward(reader, writer, pinned_host, address, resolve))
        active[task] = writer
        task.add_done_callback(active.pop)

    server = await asyncio.start_server(accept, "127.0.0.1", 0)
    try:
        yield server.sockets[0].getsockname()[1]
    finally:
        closing = True
        server.close()
        # A disposed browser may stop reading with bytes still buffered.
        for task, writer in active.items():
            writer.transport.abort()
            task.cancel()
        await asyncio.gather(*active, return_exceptions=True)
        await server.wait_closed()
