import os
import json
import logging
from google import genai
from google.genai import types

log = logging.getLogger(__name__)

# Use gemini-2.5-flash - latest stable model
MODEL = "models/gemini-2.5-flash"

def client():
    """Get Gemini client with API key from environment."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment variables")
    return genai.Client(api_key=api_key)

def generate_json(user_text: str, system_prompt: str) -> dict:
    """Generate JSON response from Gemini using the system prompt."""
    try:
        c = client()
        response = c.models.generate_content(
            model=MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_text)]
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,
            )
        )
        text = response.text or ""
        if not text:
            log.error("Empty response from Gemini API")
            raise ValueError("No response from API")
        
        # Try to extract JSON from the response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse JSON response: {e}\nResponse text: {text}")
        raise
    except Exception as e:
        log.error(f"LLM call failed: {type(e).__name__}: {e}")
        raise


def generate_text(user_text: str, system_prompt: str) -> str:
    """Generate free-form text response from Gemini using the system prompt."""
    try:
        c = client()
        response = c.models.generate_content(
            model=MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_text)]
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            )
        )
        return (response.text or "").strip()
    except Exception as e:
        log.error(f"LLM generate_text failed: {type(e).__name__}: {e}")
        raise

