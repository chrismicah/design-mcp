"""Exercise a competitor's discovered stdio search surface with fixed queries."""

import argparse
import asyncio
import json
from pathlib import Path
import time

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

QUERIES = ('mobile checkout progress', 'accessible account settings error state',
           'B2B pricing comparison', 'zzqv_74f18')


async def probe(args):
    transport = StdioTransport(command=args.command[0], args=args.command[1:], cwd=str(args.cwd))
    receipts = {}
    async with Client(transport, timeout=40) as client:
        tools = await client.list_tools()
        schemas = {tool.name: tool.inputSchema for tool in tools}
        if args.tool not in schemas:
            raise RuntimeError(f'{args.tool} is absent. Discovered tools: {sorted(schemas)}')
        for query in QUERIES:
            start = time.monotonic()
            try:
                result = await client.call_tool(args.tool, {'query': query, 'limit': 3, **args.fields})
                content = [block.model_dump(mode='json') for block in result.content]
                preview = '\n'.join(block.get('text', '') for block in content)[:2200]
                receipts[query] = {'status': 'success', 'milliseconds': round((time.monotonic() - start)*1000),
                                   'bytes': len(json.dumps(content).encode('utf-8')), 'text_preview': preview}
            except Exception as error:
                receipts[query] = {'status': 'error', 'message': str(error)[:800]}
    return {'server_tool': args.tool, 'tools': schemas, 'queries': receipts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cwd', type=Path, required=True)
    parser.add_argument('--tool', required=True)
    parser.add_argument('--fields', type=json.loads, default={})
    parser.add_argument('command', nargs='+')
    args = parser.parse_args()
    result = asyncio.run(probe(args))
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(f'{len(result["tools"])} tools, {sum(cell["status"] == "success" for cell in result["queries"].values())}/4 queries returned')


if __name__ == '__main__':
    main()
