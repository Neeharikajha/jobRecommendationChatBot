from chat.models import Resume, Application
from .matcher import search_jobs as _search, get_job

TOOL_DECLS = [
    {"name": "search_jobs",
     "description": "Find jobs matching the user's resume, optionally filtered. Call again with new filters to refine.",
     "parameters": {"type": "object", "properties": {
         "remote": {"type": "boolean", "description": "true for remote-only"},
         "skills": {"type": "array", "items": {"type": "string"}, "description": "required skills, e.g. ['react']"},
         "location": {"type": "string"},
         "keyword": {"type": "string", "description": "word in title/description"},
         "limit": {"type": "integer"}}}},
    {"name": "get_job_details",
     "description": "Get full details of one job by job_id.",
     "parameters": {"type": "object", "properties": {"job_id": {"type": "integer"}}, "required": ["job_id"]}},
    {"name": "apply_to_job",
     "description": "Apply to a job by job_id and record the application.",
     "parameters": {"type": "object", "properties": {"job_id": {"type": "integer"}}, "required": ["job_id"]}},
    {"name": "get_applications",
     "description": "List all jobs the user has applied to, with date and status.",
     "parameters": {"type": "object", "properties": {}}},
]


def _resume(sid):
    r = Resume.objects.filter(session_key=sid).first()
    return r.data if r else {}

def search_jobs_tool(sid, **args):
    return _search(_resume(sid), **args)

def get_job_details(sid, job_id):
    job = get_job(int(job_id))
    return job if job else {"error": f"Job {job_id} not found"}

def apply_to_job(sid, job_id):
    try:
        job_id = int(job_id)
    except (TypeError, ValueError):
        return {"error": "invalid job id"}
    job = get_job(job_id)
    if not job:
        return {"error": f"Job {job_id} does not exist."}
    app, created = Application.objects.get_or_create(
        session_key=sid, job_id=job_id,
        defaults={"job_title": job["title"], "company": job["company"]})
    if not created:
        return {"error": f"You already applied to job {job_id} on {app.applied_at:%d %b %Y}."}
    return {"ok": True, "job_id": job_id, "title": job["title"], "company": job["company"],
            "status": app.status, "applied_at": f"{app.applied_at:%d %b %Y}"}

def get_applications(sid):
    apps = Application.objects.filter(session_key=sid).order_by("-applied_at")
    if not apps:
        return {"count": 0, "message": "No applications yet."}
    return {"count": apps.count(), "applications": [
        {"job_id": a.job_id, "title": a.job_title, "company": a.company,
         "applied_at": f"{a.applied_at:%d %b %Y}", "status": a.status} for a in apps]}

def run_tool(name, args, sid):
    try:
        if name == "search_jobs":
            if "skills" in args:
                args["skills"] = list(args["skills"])
            return search_jobs_tool(sid, **args)
        if name == "get_job_details":
            return get_job_details(sid, **args)
        if name == "apply_to_job":
            return apply_to_job(sid, **args)
        if name == "get_applications":
            return get_applications(sid)
        return {"error": f"Unknown tool {name}"}
    except TypeError:
        return {"error": "Invalid tool arguments."}
    except Exception:
        return {"error": "Tool failed unexpectedly."}