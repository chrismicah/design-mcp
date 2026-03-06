import asyncio, json, sys
sys.stdout.reconfigure(encoding='utf-8')
from server import (
    scan_project, search_design_patterns, get_semantic_tokens,
    get_behavioral_pattern, analyze_and_devibecode, get_design_blueprint
)

async def test():
    # 1. Scan the lawyer project
    print('=' * 60)
    print('STEP 1: SCAN PROJECT')
    print('=' * 60)
    scan = await scan_project('C:/Users/15046/Projects/lawyer-dashboard/src')
    print(json.dumps(scan, indent=2, default=str, ensure_ascii=False)[:4000])
    
    # 2. Search for dashboard patterns
    print('\n' + '=' * 60)
    print('STEP 2: SEARCH DASHBOARD PATTERNS')
    print('=' * 60)
    results = await search_design_patterns('law firm dashboard', page_type='Dashboard', limit=3)
    for r in results:
        has_tokens = bool(r.get('semantic_tokens'))
        has_behavior = bool(r.get('behavioral_description'))
        has_a11y = bool(r.get('accessibility_notes'))
        has_hints = bool(r.get('component_hints'))
        print(f"  {r['name']}: tokens={has_tokens}, behavior={has_behavior}, a11y={has_a11y}, hints={has_hints}")
    
    if results:
        # 3. Get full blueprint for top result
        print('\n' + '=' * 60)
        print('STEP 3: FULL BLUEPRINT FOR TOP RESULT')
        print('=' * 60)
        bp = await get_design_blueprint(results[0]['id'], detailed=True)
        print(json.dumps(bp, indent=2, default=str, ensure_ascii=False)[:3000])
    
    # 4. Get semantic tokens
    print('\n' + '=' * 60)
    print('STEP 4: SEMANTIC TOKENS (DARK)')
    print('=' * 60)
    tokens = await get_semantic_tokens('dark')
    if isinstance(tokens, dict) and 'dark' in tokens:
        dark = tokens['dark']
    else:
        dark = tokens
    for k, v in list(dark.items())[:15]:
        print(f"  {k}: {v}")
    
    # 5. Get behavioral pattern
    print('\n' + '=' * 60)
    print('STEP 5: BEHAVIORAL PATTERN - DASHBOARD')
    print('=' * 60)
    bp = await get_behavioral_pattern('dashboard')
    print(json.dumps(bp, indent=2, ensure_ascii=False)[:2000])
    
    # 6. Analyze a specific file
    print('\n' + '=' * 60)
    print('STEP 6: ANALYZE DASHBOARD PAGE')
    print('=' * 60)
    with open('C:/Users/15046/Projects/lawyer-dashboard/src/app/dashboard/page.tsx') as f:
        code = f.read()
    analysis = await analyze_and_devibecode(code[:3000], 'tsx')
    print(json.dumps(analysis, indent=2, default=str, ensure_ascii=False)[:3000])

asyncio.run(test())
