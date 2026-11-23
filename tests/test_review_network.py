import asyncio
import ipaddress
import socket
import unittest
from unittest.mock import patch

from design_mcp.review import network


async def connect(proxy_port, host, port):
    reader, writer = await asyncio.open_connection("127.0.0.1", proxy_port)
    try:
        writer.write(b"\x05\x01\x00")
        assert await reader.readexactly(2) == b"\x05\x00"
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            name = host.encode("ascii")
            destination = bytes((3, len(name))) + name
        else:
            destination = bytes((1 if ip.version == 4 else 4,)) + ip.packed
        writer.write(b"\x05\x01\x00" + destination + port.to_bytes(2, "big"))
        await writer.drain()
        result = await asyncio.wait_for(reader.readexactly(10), 2)
        return reader, writer, result[1]
    except BaseException:
        writer.close()
        raise


class ProxyTests(unittest.IsolatedAsyncioTestCase):
    async def test_context_shutdown_closes_client_waiting_after_socks_greeting(self):
        writer = None

        async def finish_review():
            nonlocal writer
            async with network.public_proxy("example.com", "93.184.216.34", None) as proxy:
                reader, writer = await asyncio.open_connection("127.0.0.1", proxy)
                writer.write(b"\x05\x01\x00")
                await writer.drain()
                self.assertEqual(await reader.readexactly(2), b"\x05\x00")
            return reader

        try:
            # Leave the socket open through context exit.
            reader = await asyncio.wait_for(finish_review(), 1)
            self.assertEqual(await asyncio.wait_for(reader.read(), 1), b"")
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()

    async def test_shutdown_aborts_output_to_a_client_that_stops_reading(self):
        owned = asyncio.get_running_loop().create_future()
        client = None

        async def queue_output(reader, writer, *_):
            peer_socket = writer.get_extra_info("socket")
            peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
            writer.write(b"x" * 1_048_576)
            owned.set_result(writer)
            await writer.drain()

        async def finish_review():
            nonlocal client
            async with network.public_proxy("example.com", "93.184.216.34", None) as proxy:
                _, client = await asyncio.open_connection("127.0.0.1", proxy)
                client.transport.pause_reading()
                peer = await owned
                self.assertGreater(peer.transport.get_write_buffer_size(), 0)
            self.assertEqual(peer.transport.get_write_buffer_size(), 0)

        with patch.object(network, "_forward", side_effect=queue_output):
            try:
                await asyncio.wait_for(finish_review(), 1)
            finally:
                if client is not None:
                    client.transport.abort()
                    await client.wait_closed()

    async def test_refuses_private_and_mixed_dns_destinations_before_connecting(self):
        lookups = []

        def resolve(host, port, type):
            lookups.append(host)
            return [(socket.AF_INET, type, 6, "", (value, port))
                    for value in ("93.184.216.34", "127.0.0.1")]

        with patch.object(network, "open_connection") as upstream:
            async with network.public_proxy("page.example", "93.184.216.34", resolve) as proxy:
                for host in ("assets.example", "127.0.0.1", "fd00::1", "::ffff:127.0.0.1", "2002::1",
                             "224.0.0.1", "printer.local."):
                    with self.subTest(host=host):
                        reader, writer, result = await connect(proxy, host, 443)
                        try:
                            self.assertEqual(result, 2)
                            self.assertEqual(await asyncio.wait_for(reader.read(), 2), b"")
                        finally:
                            writer.close()
                            await writer.wait_closed()
        upstream.assert_not_called()
        self.assertEqual(lookups, ["assets.example"])

    async def test_connects_only_to_the_checked_numeric_address_and_relays_bytes(self):
        lookups = []

        def resolve(host, port, type):
            lookups.append(host)
            return [(socket.AF_INET, type, 6, "", ("8.8.8.8", port))]

        async def echo(reader, writer):
            try:
                writer.write(await reader.readexactly(4))
                await writer.drain()
            finally:
                writer.close()

        server = await asyncio.start_server(echo, "127.0.0.1", 0)
        async with server:
            port = server.sockets[0].getsockname()[1]

            async def fixture_connection(address, port, *, flags):
                self.assertEqual(flags, socket.AI_NUMERICHOST)
                return await asyncio.open_connection("127.0.0.1", port)

            with patch.object(network, "open_connection", side_effect=fixture_connection) as upstream:
                async with network.public_proxy("page.example", "93.184.216.34", resolve) as proxy:
                    for host in ("Page.Example.", "assets.example"):
                        reader, writer, result = await connect(proxy, host, port)
                        try:
                            self.assertEqual(result, 0)
                            writer.write(b"ping")
                            await writer.drain()
                            self.assertEqual(await asyncio.wait_for(reader.readexactly(4), 2), b"ping")
                        finally:
                            writer.close()
                            await writer.wait_closed()
            self.assertEqual([call.args for call in upstream.call_args_list],
                             [("93.184.216.34", port), ("8.8.8.8", port)])
            self.assertEqual(lookups, ["assets.example"])
