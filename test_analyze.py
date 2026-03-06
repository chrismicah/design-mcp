import asyncio, json, sys
sys.stdout.reconfigure(encoding='utf-8')
from server import analyze_and_devibecode

async def test():
    with open('C:/Users/15046/Projects/lawyer-dashboard/src/app/dashboard/page.tsx') as f:
        code = f.read()
    analysis = await analyze_and_devibecode(code[:3000])
    print(json.dumps(analysis, indent=2, default=str, ensure_ascii=False)[:5000])

asyncio.run(test())
