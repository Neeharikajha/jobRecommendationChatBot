import json
import logging
from google.genai import types
from chat.models import Resume, Message
from .llm import client, MODEL
from .prompts import AGENT_SYSTEM
from .tools import TOOL_DECLS, run_tool

log = logging.getLogger(__name__)
MAX_STEPS = 6
HISTORY = 12

def run_agent(sid: str, user_text: str) -> str:
    r = Resume.objects.filter(session_key=sid).first()
    resume_txt = json.dumps(r.data) if r else "none uploaded"

    history = list(Message.objects.filter(session_key=sid).order_by("-id")[:HISTORY])[::-1]
    while history and history[0].role != "user":
        history.pop(0)
    contents = [types.Content(role=m.role, parts=[types.Part(text=m.content)]) for m in history]
    contents.append(types.Content(role="user", parts=[types.Part(text=user_text)]))

    config = types.GenerateContentConfig(
        system_instruction=AGENT_SYSTEM.format(resume=resume_txt),
        tools=[types.Tool(function_declarations=TOOL_DECLS)],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        temperature=0.3,
    )

    reply = None
    try:
        for step in range(MAX_STEPS):
            try:
                resp = client().models.generate_content(model=MODEL, contents=contents, config=config)
            except Exception as e:
                log.error(f"API call failed at step {step}: {type(e).__name__}: {e}")
                raise
            
            calls = resp.function_calls
            if not calls:
                reply = resp.text or "Sorry, I couldn't come up with a response."
                break
            
            contents.append(resp.candidates[0].content)
            parts = []
            for c in calls:
                try:
                    tool_result = run_tool(c.name, dict(c.args or {}), sid)
                    parts.append(types.Part.from_function_response(
                        name=c.name, 
                        response={"result": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)}
                    ))
                except Exception as e:
                    log.error(f"Tool {c.name} failed: {e}")
                    parts.append(types.Part.from_function_response(
                        name=c.name,
                        response={"error": str(e)}
                    ))
            
            contents.append(types.Content(role="user", parts=parts))
        else:
            reply = "That took too many steps. Could you rephrase?"
    except Exception as e:
        log.exception(f"agent failed: {type(e).__name__}: {e}")
        return "I'm having trouble reaching the AI service. Please try again in a moment."

    try:
        Message.objects.create(session_key=sid, role="user", content=user_text)
        Message.objects.create(session_key=sid, role="model", content=reply)
    except Exception as e:
        log.error(f"Failed to save messages: {e}")
    
    return reply