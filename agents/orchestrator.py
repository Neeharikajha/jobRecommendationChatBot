import json
import logging
import re
from datetime import datetime
from chat.models import Resume, Message, Application
from .llm import generate_json
from .matcher import search_jobs, get_job

log = logging.getLogger(__name__)

def run_agent(sid: str, user_text: str) -> str:
    """Run agent - handles job search and applications directly."""
    try:
        r = Resume.objects.filter(session_key=sid).first()
        resume_data = r.data if r else {}
        
        # Check for application request
        apply_match = re.search(r'apply\s+(?:to\s+)?job\s+(\d+)', user_text.lower())
        if apply_match:
            job_id = int(apply_match.group(1))
            job = get_job(job_id)
            if not job:
                reply = f"Job {job_id} not found."
            else:
                app, created = Application.objects.get_or_create(
                    session_key=sid,
                    job_id=job_id,
                    defaults={
                        "job_title": job.get("title", ""),
                        "company": job.get("company", "")
                    }
                )
                if created:
                    reply = f"✅ Applied to {job.get('title')} at {job.get('company')}\n\nApplication recorded on {app.applied_at.strftime('%d %b %Y')}"
                else:
                    reply = f"You already applied to this job on {app.applied_at.strftime('%d %b %Y')}"
        
        # Check for application history request
        elif any(word in user_text.lower() for word in ["show", "list", "my", "applied", "applications", "history"]):
            apps = Application.objects.filter(session_key=sid).order_by("-applied_at")
            if not apps:
                reply = "No applications yet. Try searching for jobs first!"
            else:
                app_list = "\n".join([
                    f"- {a.job_title} at {a.company} ({a.applied_at.strftime('%d %b %Y')})"
                    for a in apps[:10]
                ])
                reply = f"Your applications ({apps.count()}):\n{app_list}"
        
        # Check for job search/recommendation request
        elif any(word in user_text.lower() for word in ["search", "find", "jobs", "recommend", "match", "show"]):
            if not resume_data:
                reply = "Please upload your resume first to get job recommendations."
            else:
                # Check for filters
                remote_only = "remote" in user_text.lower()
                
                # Check for skill filters
                skills_filter = None
                skill_match = re.search(r'(?:need|require|with|for)\s+([\w\s,]+)', user_text.lower())
                if skill_match:
                    skills_filter = [s.strip() for s in skill_match.group(1).split(",")]
                
                try:
                    results = search_jobs(
                        resume_data,
                        remote=remote_only if remote_only else None,
                        skills=skills_filter,
                        limit=10
                    )
                    
                    if results["count"] == 0:
                        reply = "No jobs match your criteria. Try adjusting your filters!"
                    else:
                        job_list = "\n".join([
                            f"**{i+1}. {job['title']}** at {job['company']}\n"
                            f"   Location: {job['location']} {'(Remote)' if job['remote'] else ''}\n"
                            f"   Match: {job['match_reason']}"
                            for i, job in enumerate(results["jobs"])
                        ])
                        reply = f"Found {results['count']} matching jobs:\n\n{job_list}\n\n" \
                               f"Type 'apply to job 1' to apply, or refine with 'show remote roles' or 'jobs with Python'"
                except Exception as e:
                    log.error(f"Search failed: {e}")
                    reply = f"Search failed: {str(e)}"
        
        # Default: conversational response
        else:
            system_prompt = f"""You are a helpful job search assistant.
User's resume: {json.dumps(resume_data) if resume_data else "No resume uploaded yet"}

Respond conversationally to the user's message about their job search.
Keep responses brief and helpful."""
            
            try:
                response = generate_json(user_text, system_prompt)
                if isinstance(response, dict):
                    reply = response.get("response") or response.get("message") or str(response)
                else:
                    reply = str(response)
            except Exception as e:
                log.error(f"Conversational response failed: {e}")
                reply = "How can I help you with your job search? Try 'find jobs', 'apply to job 1', or 'show my applications'"
        
    except Exception as e:
        log.exception(f"Agent error: {e}")
        reply = f"Error: {str(e)[:100]}"
    
    # Save message to history
    try:
        Message.objects.create(session_key=sid, role="user", content=user_text)
        Message.objects.create(session_key=sid, role="model", content=reply)
    except Exception as e:
        log.error(f"Failed to save messages: {e}")
    
    return reply
