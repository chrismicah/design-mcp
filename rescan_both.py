import asyncio, json, sys, subprocess, os
sys.stdout.reconfigure(encoding='utf-8')
from server import scan_project

async def test():
    lawyer_dir = 'C:/Users/15046/Projects/lawyer-dashboard'
    
    # Scan current state (MCP-improved)
    print('=== AFTER MCP IMPROVEMENTS ===')
    scan_after = await scan_project(f'{lawyer_dir}/src')
    print(f"Health Score: {scan_after['project_health_score']}/100")
    print(f"Issues: {scan_after['total_issues']} ({scan_after['severity_summary']})")
    for issue in scan_after['top_issues']:
        print(f"  {issue['type']}: {issue['count']}")
    
    # Checkout baseline
    os.chdir(lawyer_dir)
    subprocess.run(['git', 'checkout', 'cb1f2f3', '--', 'src/'], capture_output=True)
    
    print('\n=== BEFORE (BASELINE) ===')
    scan_before = await scan_project(f'{lawyer_dir}/src')
    print(f"Health Score: {scan_before['project_health_score']}/100")
    print(f"Issues: {scan_before['total_issues']} ({scan_before['severity_summary']})")
    for issue in scan_before['top_issues']:
        print(f"  {issue['type']}: {issue['count']}")
    
    # Restore improved version
    subprocess.run(['git', 'checkout', 'HEAD', '--', 'src/'], capture_output=True)
    
    print(f'\n=== DELTA ===')
    print(f"Score: {scan_before['project_health_score']} -> {scan_after['project_health_score']}")
    print(f"Issues: {scan_before['total_issues']} -> {scan_after['total_issues']}")

asyncio.run(test())
