#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from agents.matcher import load_jobs, search_jobs
from chat.models import Application

jobs = load_jobs()
print(f'Total jobs: {len(jobs)}')
print('\nFirst 3 jobs:')
for job in jobs[:3]:
    job_id = job.get('id') or job.get('job_id')
    print(f'  ID: {job_id} - {job.get("title")}')

print('\n\nFrontend jobs:')
frontend_jobs = [j for j in jobs if 'frontend' in j.get('title', '').lower()]
print(f'Found {len(frontend_jobs)} frontend jobs')
for i, job in enumerate(frontend_jobs[:5]):
    job_id = job.get('id') or job.get('job_id')
    print(f'  {i+1}. ID: {job_id} - {job.get("title")}')

print('\n\nApplications in DB:')
apps = Application.objects.all()
for app in apps[:5]:
    print(f'  Job ID: {app.job_id} - {app.job_title} at {app.company}')
