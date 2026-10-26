import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from agents.orchestrator import classify_intent, extract_role_type, extract_display_ids, extract_limit

print("=== Intent Classification Tests ===")
tests = [
    ("show me frontend developer roles", "search_jobs"),
    ("what roles can I apply to", "profile_roles"),
    ("based on my profile what jobs can i apply", "profile_roles"),
    ("give me only frontend developer roles only 7", "search_jobs"),
    ("show my applied jobs", "view_applications"),
    ("apply to jobs 1, 2, 3", "apply_jobs"),
    ("remove job 2", "remove_application"),
    ("what am I eligible for", "profile_roles"),
    ("find remote react jobs", "search_jobs"),
]
all_ok = True
for msg, expected in tests:
    got = classify_intent(msg)
    status = "OK" if got == expected else "FAIL"
    if status == "FAIL":
        all_ok = False
    print(f"  [{status}] '{msg}' -> {got} (expected: {expected})")

print()
print("=== Role Type Extraction ===")
role_tests = [
    ("give me only frontend developer roles only 7", "frontend"),
    ("show backend jobs", "backend"),
    ("find full stack developer roles", "fullstack"),
    ("show me jobs", None),
]
for msg, expected in role_tests:
    got = extract_role_type(msg)
    status = "OK" if got == expected else "FAIL"
    print(f"  [{status}] '{msg}' -> {got} (expected: {expected})")

print()
print("=== Limit Extraction ===")
limit_tests = [
    ("give me only frontend developer roles only 7", 7),
    ("show 5 jobs", 5),
    ("find me 3 remote roles", 3),
    ("show jobs", 10),
]
for msg, expected in limit_tests:
    got = extract_limit(msg)
    status = "OK" if got == expected else "FAIL"
    print(f"  [{status}] '{msg}' -> {got} (expected: {expected})")

print()
print("=== Display ID Extraction ===")
id_tests = [
    ("apply to 1, 2, 3", [1, 2, 3]),
    ("apply to jobs 1 and 3", [1, 3]),
    ("apply 5", [5]),
]
for msg, expected in id_tests:
    got = extract_display_ids(msg)
    status = "OK" if got == expected else "FAIL"
    print(f"  [{status}] '{msg}' -> {got} (expected: {expected})")
