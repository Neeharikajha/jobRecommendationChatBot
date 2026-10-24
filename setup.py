#!/usr/bin/env python
"""Complete setup script - run this once to get everything working."""

import os
import sys
import subprocess
from pathlib import Path

print("=" * 70)
print("🚀 AI JOB ASSISTANT - COMPLETE SETUP")
print("=" * 70)

# Step 1: Check .env
print("\n[1/5] Checking .env file...")
env_file = Path(".env")
if not env_file.exists():
    print("❌ .env file not found!")
    print("Please create .env with:")
    print("  GEMINI_API_KEY=your_key_here")
    print("  SECRET_KEY=any-long-random-string")
    print("  DEBUG=True")
    sys.exit(1)

# Check if API key is set
with open(".env") as f:
    content = f.read()
    if "GEMINI_API_KEY=" not in content or "your_key_here" in content:
        print("❌ GEMINI_API_KEY not properly set in .env")
        sys.exit(1)

print("✅ .env file exists and has API key")

# Step 2: Load environment
print("\n[2/5] Loading environment...")
from dotenv import load_dotenv
load_dotenv()
print("✅ Environment loaded")

# Step 3: Run migrations
print("\n[3/5] Creating database tables...")
try:
    result = subprocess.run(
        [sys.executable, "manage.py", "migrate"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ Migration failed:")
        print(result.stderr)
        sys.exit(1)
    print("✅ Database tables created")
except Exception as e:
    print(f"❌ Error running migrations: {e}")
    sys.exit(1)

# Step 4: Verify database
print("\n[4/5] Verifying database...")
try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    from chat.models import Resume, Application, Message
    print("✅ Database tables verified")
except Exception as e:
    print(f"❌ Database verification failed: {e}")
    sys.exit(1)

# Step 5: Test Gemini API
print("\n[5/5] Testing Gemini API...")
try:
    from google import genai
    from google.genai import types
    
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text="Say 'OK'")]
            )
        ]
    )
    
    if response.text:
        print("✅ Gemini API working")
    else:
        print("❌ Gemini API returned empty response")
        sys.exit(1)
except Exception as e:
    print(f"❌ Gemini API test failed: {e}")
    print("   Make sure your API key is valid")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL SETUP COMPLETE!")
print("=" * 70)
print("\nNow run:")
print("  python manage.py runserver")
print("\nThen open:")
print("  http://localhost:8000")
print("=" * 70)
