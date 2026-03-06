import asyncio, json, sys
sys.stdout.reconfigure(encoding='utf-8')
from server import scan_project

async def test():
    scan = await scan_project('C:/Users/15046/Projects/lawyer-dashboard/src')
    print(f"Health Score: {scan['project_health_score']}/100")
    print(f"Files scanned: {scan['files_scanned']}")
    print(f"Files with issues: {scan['files_with_issues']}")
    print(f"Total issues: {scan['total_issues']}")
    print(f"Severity: {scan['severity_summary']}")
    print(f"\nTop issues:")
    for issue in scan['top_issues']:
        print(f"  {issue['type']}: {issue['count']}")

asyncio.run(test())
