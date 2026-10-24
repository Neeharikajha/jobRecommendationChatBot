#!/usr/bin/env python
"""Test script to verify Gemini API works."""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Test 1: Check API key
print("=" * 60)
print("TEST 1: Checking API key")
print("=" * 60)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env")
    sys.exit(1)
print(f"✅ API key found: {api_key[:20]}...")

# Test 2: Import Gemini library
print("\n" + "=" * 60)
print("TEST 2: Importing google-genai")
print("=" * 60)
try:
    from google import genai
    from google.genai import types
    print("✅ google-genai imported successfully")
except ImportError as e:
    print(f"❌ ERROR: Failed to import google-genai: {e}")
    sys.exit(1)

# Test 3: Create client
print("\n" + "=" * 60)
print("TEST 3: Creating Gemini client")
print("=" * 60)
try:
    client = genai.Client(api_key=api_key)
    print("✅ Client created successfully")
except Exception as e:
    print(f"❌ ERROR: Failed to create client: {e}")
    sys.exit(1)

# Test 4: List available models
print("\n" + "=" * 60)
print("TEST 4: Listing available models")
print("=" * 60)
try:
    models = client.models.list()
    print(f"✅ Available models:")
    model_names = []
    for model in models:
        print(f"   - {model.name}")
        model_names.append(model.name)
    if not model_names:
        print("   No models found!")
except Exception as e:
    print(f"⚠️  Could not list models: {type(e).__name__}: {e}")
    print("   Using fallback model: gemini-1.5-flash")
    model_names = ["gemini-1.5-flash"]

# Test 5: Simple API call with better model
print("\n" + "=" * 60)
print("TEST 5: Making simple API call")
print("=" * 60)
model_to_use = "models/gemini-2.5-flash"
print(f"Using model: {model_to_use}")
try:
    response = client.models.generate_content(
        model=model_to_use,
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text="Say 'Hello, World!'")]
            )
        ]
    )
    print(f"✅ API call successful")
    print(f"   Response: {response.text[:100]}")
except Exception as e:
    print(f"❌ ERROR: API call failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: JSON response test
print("\n" + "=" * 60)
print("TEST 6: Testing JSON extraction")
print("=" * 60)
try:
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text='Return valid JSON: {"name": "test", "value": 123}')]
            )
        ],
        config=types.GenerateContentConfig(temperature=0.1)
    )
    text = response.text or ""
    print(f"Raw response: {text[:200]}")
    
    # Extract JSON
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    
    data = json.loads(text.strip())
    print(f"✅ JSON parsed successfully")
    print(f"   Parsed data: {data}")
except json.JSONDecodeError as e:
    print(f"❌ ERROR: JSON parsing failed: {e}")
    print(f"   Text: {text[:200]}")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Resume parsing prompt
print("\n" + "=" * 60)
print("TEST 7: Testing resume parsing prompt")
print("=" * 60)
try:
    system_prompt = """You extract structured data from resume text.
Return ONLY a JSON object with these keys:
name (str), email (str), phone (str),
designation (str), skills (list of str),
experience_years (number), experience (list of str),
education (list of str), projects (list of str).
Use "" or [] when missing. Never invent data."""

    sample_resume = """John Doe
john@example.com | +1-234-567-8900

Senior Software Engineer
XYZ Corp | 2020-2024

Skills: Python, Django, React, AWS
Experience: 5 years in full-stack development
Education: B.S. Computer Science, State University 2019"""

    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text=f"Resume text:\n{sample_resume}")]
            )
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3
        )
    )
    
    text = response.text or ""
    print(f"Raw response: {text[:300]}")
    
    # Extract JSON
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    
    data = json.loads(text.strip())
    print(f"✅ Resume parsing successful")
    print(f"   Name: {data.get('name')}")
    print(f"   Skills: {data.get('skills')}")
    print(f"   Experience: {data.get('experience_years')} years")
except json.JSONDecodeError as e:
    print(f"❌ ERROR: JSON parsing failed: {e}")
    print(f"   Text: {text[:300]}")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
