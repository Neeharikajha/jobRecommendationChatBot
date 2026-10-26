import logging
import re
from chat.models import Resume, Message, Application
from .matcher import search_jobs, get_job

log = logging.getLogger(__name__)

_SESSION_JOB_MAP  = "last_job_map"   # {display_num_str: real_job_id_int}
_SESSION_JOB_LIST = "last_job_list"  # [job_id, ...]


# ─── INTENT CLASSIFIER ───────────────────────────────────────────────────────

def classify_intent(user_text: str) -> str:
    text = user_text.lower()

    if any(w in text for w in ["remove", "withdraw", "delete", "cancel", "undo"]):
        if any(c.isdigit() for c in user_text):
            return "remove_application"

    if any(w in text for w in ["apply to", "apply for", "apply job", "submit application", "apply"]):
        if any(c.isdigit() for c in user_text):
            return "apply_jobs"

    if any(w in text for w in [
        "applied", "my applications", "application history",
        "where have i applied", "which jobs have i", "show applied",
        "track", "applications"
    ]):
        return "view_applications"

    if any(p in text for p in [
        "what roles", "which roles", "what jobs", "which jobs", "what position",
        "what can i apply", "what should i apply", "roles can i apply",
        "suitable roles", "eligible for", "profile match",
        "based on my profile", "based on experience", "what am i eligible",
        "titles", "which title"
    ]):
        return "profile_roles"

    if any(w in text for w in [
        "search", "find", "show", "give", "get", "recommend", "suggest",
        "jobs", "roles", "position", "opportunities", "openings",
        "developer", "engineer", "frontend", "backend", "fullstack",
        "full stack", "remote", "python", "react", "java", "related to",
        "profile", "match", "more", "different"
    ]):
        if not any(w in text for w in ["applied", "application history"]):
            return "search_jobs"

    return "other"


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def extract_display_ids(user_text: str) -> list[int]:
    text = re.sub(r'\s+and\s+', ', ', user_text.lower())
    text = re.sub(r'\s+or\s+', ', ', text)
    return [int(n) for n in re.findall(r'\d+', text)]


def extract_limit(user_text: str) -> int:
    text = user_text.lower()
    for pattern in [
        r'only\s+(\d+)',
        r'(\d+)\s+(?:jobs?|more|results?|positions?|roles?|opportunities?)',
        r'(?:give|show|find|search)\s+(?:me\s+)?(\d+)',
    ]:
        m = re.search(pattern, text)
        if m:
            return int(m.group(1))
    return 10


def extract_role_type(user_text: str) -> str | None:
    t = user_text.lower()
    if any(k in t for k in ["frontend", "front-end", "front end", "react developer", "ui developer"]):
        return "frontend"
    if any(k in t for k in ["backend", "back-end", "back end"]):
        return "backend"
    if any(k in t for k in ["fullstack", "full stack", "full-stack"]):
        return "fullstack"
    if any(k in t for k in ["devops", "sre", "cloud engineer"]):
        return "devops"
    if any(k in t for k in ["data science", "machine learning", "ml engineer", "ai engineer"]):
        return "data"
    if any(k in t for k in ["mobile", "android", "ios", "flutter"]):
        return "mobile"
    return None


def extract_skills_filter(user_text: str) -> list | None:
    t = user_text.lower()
    known = [
        "react", "angular", "vue", "javascript", "typescript", "html", "css",
        "python", "java", "node", "express", "django", "fastapi", "spring",
        "aws", "azure", "gcp", "docker", "kubernetes", "postgres", "mysql",
        "mongodb", "golang", "rust", "flutter", "kotlin", "swift",
    ]
    found = [s for s in known if re.search(rf'\b{re.escape(s)}\b', t)]
    return found if found else None


# ─── MAIN AGENT ──────────────────────────────────────────────────────────────

def run_agent(sid: str, user_text: str, request=None) -> dict:
    """
    Returns a dict:
      {
        "reply": str,            # plain text / markdown for the chat bubble
        "type": str,             # "text" | "jobs" | "applications" | "roles"
        "jobs": list | None,     # structured job list when type == "jobs"
        "applications": list | None,
      }
    """
    result = {"reply": "", "type": "text", "jobs": None, "applications": None}

    try:
        r = Resume.objects.filter(session_key=sid).first()
        resume_data = r.data if r else {}

        intent = classify_intent(user_text)
        log.info(f"Intent: {intent!r} | {user_text[:60]}")

        session = request.session if request else None
        job_map: dict = {}
        if session:
            raw = session.get(_SESSION_JOB_MAP, {})
            job_map = {str(k): int(v) for k, v in raw.items()} if raw else {}

        # ── APPLY ─────────────────────────────────────────────────────────
        if intent == "apply_jobs":
            display_ids = extract_display_ids(user_text)
            if not display_ids:
                result["reply"] = (
                    "Please specify which job numbers to apply to. "
                    "Example: 'apply to 1, 2, 3'"
                )
            else:
                applied, already, not_found = [], [], []

                for d_id in display_ids:
                    real_id = job_map.get(str(d_id))
                    if real_id is None:
                        job = get_job(d_id)
                        real_id = d_id if job else None
                    else:
                        job = get_job(real_id)

                    if not job:
                        not_found.append(d_id)
                        continue

                    app, created = Application.objects.get_or_create(
                        session_key=sid,
                        job_id=real_id,
                        defaults={"job_title": job.get("title", ""), "company": job.get("company", "")}
                    )
                    if created:
                        applied.append({
                            "display_id": d_id,
                            "title": job.get("title", ""),
                            "company": job.get("company", ""),
                            "source_link": job.get("source_link", ""),
                            "date": app.applied_at.strftime("%d %b %Y"),
                        })
                    else:
                        already.append(d_id)

                lines = []
                if applied:
                    lines.append(f"Application recorded for {len(applied)} job(s):")
                    for j in applied:
                        lines.append(f"  {j['display_id']}. {j['title']} at {j['company']} — {j['date']}")
                if already:
                    lines.append(f"Already applied to: {', '.join(map(str, already))}")
                if not_found:
                    lines.append(
                        f"Could not find job(s): {', '.join(map(str, not_found))}. "
                        "Search for jobs first, then use the numbers shown."
                    )
                result["reply"] = "\n".join(lines) or "No new applications made."

        # ── REMOVE ────────────────────────────────────────────────────────
        elif intent == "remove_application":
            display_ids = extract_display_ids(user_text)
            if not display_ids:
                result["reply"] = "Specify job numbers to remove. Example: 'remove 1, 2'"
            else:
                removed, not_applied, not_found = [], [], []
                for d_id in display_ids:
                    real_id = job_map.get(str(d_id), d_id)
                    try:
                        app = Application.objects.get(session_key=sid, job_id=real_id)
                        removed.append(f"{app.job_title} at {app.company}")
                        app.delete()
                    except Application.DoesNotExist:
                        (not_applied if get_job(real_id) else not_found).append(d_id)

                lines = []
                if removed:
                    lines.append(f"Removed {len(removed)} application(s):")
                    lines += [f"  — {r}" for r in removed]
                if not_applied:
                    lines.append(f"You had not applied to: {', '.join(map(str, not_applied))}")
                if not_found:
                    lines.append(f"Job numbers not found: {', '.join(map(str, not_found))}")
                result["reply"] = "\n".join(lines) or "Nothing to remove."

        # ── VIEW APPLICATIONS ─────────────────────────────────────────────
        elif intent == "view_applications":
            apps = Application.objects.filter(session_key=sid).order_by("-applied_at")
            if not apps.exists():
                result["reply"] = "No applications yet. Find jobs and apply!"
            else:
                result["type"] = "applications"
                result["applications"] = [
                    {
                        "index": i + 1,
                        "title": a.job_title,
                        "company": a.company,
                        "status": a.status,
                        "date": a.applied_at.strftime("%d %b %Y"),
                    }
                    for i, a in enumerate(apps[:20])
                ]
                result["reply"] = f"You have {apps.count()} application(s) on record."

        # ── PROFILE ROLES ─────────────────────────────────────────────────
        elif intent == "profile_roles":
            if not resume_data:
                result["reply"] = "Please upload your resume first so I can suggest suitable roles."
            else:
                exp = resume_data.get("experience_years", 0)
                try:
                    exp = int(exp)
                except (TypeError, ValueError):
                    exp = 0
                skills_lower = [s.lower() for s in (resume_data.get("skills") or [])]

                has_fe = any(s in skills_lower for s in ["react", "angular", "vue", "html", "css", "javascript", "typescript"])
                has_be = any(s in skills_lower for s in ["python", "django", "fastapi", "node", "java", "spring"])
                has_cloud = any(s in skills_lower for s in ["aws", "azure", "gcp", "docker", "kubernetes"])

                if exp <= 1:
                    level, base = "Fresher / Intern", ["Software Development Intern", "Graduate Trainee", "Junior Software Developer"]
                    if has_fe: base += ["Frontend Developer Intern", "Junior UI Developer"]
                    if has_be: base += ["Backend Developer Intern", "Junior Python Developer"]
                    if has_fe and has_be: base += ["Full Stack Developer Intern"]
                elif exp <= 3:
                    level, base = "Junior", ["Junior Software Developer", "Associate Software Engineer"]
                    if has_fe: base += ["Frontend Developer", "React Developer", "UI Developer"]
                    if has_be: base += ["Backend Developer", "Python Developer"]
                    if has_fe and has_be: base += ["Full Stack Developer"]
                elif exp <= 6:
                    level, base = "Mid-level", ["Software Engineer", "Software Developer"]
                    if has_fe: base += ["Frontend Developer", "UI Engineer"]
                    if has_be: base += ["Backend Developer", "API Developer"]
                    if has_fe and has_be: base += ["Full Stack Developer"]
                    if has_cloud: base += ["DevOps Engineer", "Cloud Engineer"]
                else:
                    level, base = "Senior", ["Senior Software Engineer", "Tech Lead"]
                    if has_fe: base += ["Senior Frontend Developer", "Frontend Tech Lead"]
                    if has_be: base += ["Senior Backend Developer", "Backend Tech Lead"]
                    if has_cloud: base += ["Senior DevOps Engineer", "Platform Engineer"]

                seen, unique = set(), []
                for role in base:
                    if role not in seen:
                        seen.add(role)
                        unique.append(role)

                result["type"] = "roles"
                skills_display = ", ".join((resume_data.get("skills") or [])[:8])
                roles_str = "\n".join(f"  {i+1}. {r}" for i, r in enumerate(unique[:12]))
                result["reply"] = (
                    f"Based on {exp} year(s) of experience ({level} level), "
                    f"here are roles that suit your profile:\n\n"
                    f"{roles_str}\n\n"
                    f"Skills on your resume: {skills_display}\n\n"
                    f"Try: 'find me frontend jobs' or 'show full stack roles'"
                )

        # ── SEARCH JOBS ───────────────────────────────────────────────────
        elif intent == "search_jobs":
            if not resume_data:
                result["reply"] = "Please upload your resume first so I can find matching jobs."
            else:
                remote_only = "remote" in user_text.lower()
                limit = extract_limit(user_text)
                role_type = extract_role_type(user_text)
                skills_filter = extract_skills_filter(user_text)

                if role_type and skills_filter:
                    role_kws = {"frontend", "backend", "fullstack", "devops", "mobile"}
                    skills_filter = [s for s in skills_filter if s not in role_kws] or None

                log.info(f"Search: remote={remote_only}, role_type={role_type}, skills={skills_filter}, limit={limit}")

                search_result = search_jobs(
                    resume_data,
                    remote=remote_only if remote_only else None,
                    skills=skills_filter,
                    role_type=role_type,
                    limit=limit,
                    exp_filter=True,
                )

                if search_result["count"] == 0:
                    desc = role_type or (skills_filter[0] if skills_filter else "matching")
                    result["reply"] = (
                        f"No {desc} jobs found matching your profile right now. "
                        "Try different keywords or broaden your search."
                    )
                else:
                    jobs = search_result["jobs"]

                    # Sequential display map: 1, 2, 3 ... → real job_id
                    new_map = {str(i + 1): job["job_id"] for i, job in enumerate(jobs)}
                    if session is not None:
                        session[_SESSION_JOB_MAP] = new_map
                        session[_SESSION_JOB_LIST] = [j["job_id"] for j in jobs]
                        session.modified = True

                    # Attach display index to each job
                    for i, job in enumerate(jobs):
                        job["display_id"] = i + 1

                    apply_hint = ", ".join(str(i + 1) for i in range(min(3, len(jobs))))
                    result["type"] = "jobs"
                    result["jobs"] = jobs
                    result["reply"] = (
                        f"Found {search_result['count']} job(s) matching your profile. "
                        f"Click any card to see details. "
                        f"To apply, type: 'apply to {apply_hint}'"
                    )

        # ── FALLBACK ──────────────────────────────────────────────────────
        else:
            if not resume_data:
                result["reply"] = (
                    "Upload your resume using the paperclip button to get started.\n\n"
                    "I can help you find matching jobs, filter by role or skills, "
                    "apply to positions, and track your applications."
                )
            else:
                name = resume_data.get("name", "")
                exp = resume_data.get("experience_years", 0)
                skills_preview = ", ".join((resume_data.get("skills") or [])[:5])
                greeting = f"Hi {name}! " if name else ""
                result["reply"] = (
                    f"{greeting}Here is what I can do:\n\n"
                    "  Find jobs — 'Show me developer jobs' or 'Find remote frontend roles'\n"
                    "  Filter — 'Only remote' or 'Jobs needing Python'\n"
                    "  Suitable roles — 'What roles can I apply to?'\n"
                    "  Apply — 'Apply to jobs 1, 2, 3'\n"
                    "  Track — 'Show my applied jobs'\n\n"
                    f"Profile: {exp} yr(s) experience | Skills: {skills_preview}"
                )

    except Exception as e:
        log.exception(f"Agent error: {e}")
        result["reply"] = "Something went wrong. Please try again."

    # Persist conversation
    try:
        Message.objects.create(session_key=sid, role="user", content=user_text)
        Message.objects.create(session_key=sid, role="model", content=result["reply"])
    except Exception as e:
        log.error(f"Message save failed: {e}")

    return result
