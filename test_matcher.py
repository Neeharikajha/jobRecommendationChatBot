#!/usr/bin/env python
"""Test job matcher."""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from agents.matcher import load_jobs, search_jobs

print("=" * 60)
print("TEST: Job Matcher")
print("=" * 60)

# Load jobs
print("\n[1] Loading jobs...")
try:
    jobs = load_jobs()
    print(f"✅ Loaded {len(jobs)} jobs")
except Exception as e:
    print(f"❌ Failed to load jobs: {e}")
    sys.exit(1)

# Test search with sample resume
print("\n[2] Testing search...")
resume = {
    'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'MongoDB'],
    'designation': 'Software Developer',
    'experience_years': 0
}

try:
    results = search_jobs(resume, limit=5)
    print(f"✅ Found {results['count']} matches")
    print("\nTop matches:")
    for i, job in enumerate(results['jobs'][:3], 1):
        print(f"  {i}. {job['title']}")
        print(f"     Company: {job['company']}")
        print(f"     Location: {job['location']}")
        print(f"     Match: {job['match_reason']}")
except Exception as e:
    print(f"❌ Search failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test with filters
print("\n[3] Testing search with filters (remote only)...")
try:
    results = search_jobs(resume, remote=True, limit=3)
    print(f"✅ Found {results['count']} remote jobs")
    for job in results['jobs'][:2]:
        print(f"  - {job['title']} at {job['company']}")
except Exception as e:
    print(f"❌ Filtered search failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL MATCHER TESTS PASSED")
print("=" * 60)
