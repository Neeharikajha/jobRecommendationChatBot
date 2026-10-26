import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from agents.matcher import search_jobs, _is_senior_role, _extract_min_years

resume_junior = {
    'name': 'Neeharika Jha',
    'skills': ['react', 'javascript', 'html', 'css', 'python', 'node', 'typescript'],
    'experience_years': 1,
    'designation': 'Frontend Developer'
}

print("=== TEST 1: Junior frontend search (exp=1yr, no senior roles expected) ===")
results = search_jobs(resume_junior, role_type='frontend', limit=7, exp_filter=True)
print(f"Count: {results['count']}")
senior_in_results = []
for i, j in enumerate(results['jobs'], 1):
    title = j['title']
    link = j['source_link'] or 'N/A'
    match = j['match_reason']
    is_senior = _is_senior_role(title)
    flag = " <-- SENIOR (BUG!)" if is_senior else ""
    print(f"  {i}. {title} at {j['company']} | match: {match} | link: {link[:50]}{flag}")
    if is_senior:
        senior_in_results.append(title)

if senior_in_results:
    print(f"\nBUG: Senior roles found: {senior_in_results}")
else:
    print("\nOK: No senior roles in results!")

print()
print("=== TEST 2: exp extraction ===")
cases = ["5-3 years", "0", "3+ years", "Not specified", 2, "1-2 yrs", "fresher"]
for c in cases:
    print(f"  {c!r} -> {_extract_min_years(c)}")

print()
print("=== TEST 3: General search (no filter) ===")
results2 = search_jobs(resume_junior, limit=5, exp_filter=True)
print(f"Count: {results2['count']}")
for i, j in enumerate(results2['jobs'], 1):
    print(f"  {i}. {j['title']} | exp_req={j['experience_required']} | {j['match_reason']}")
