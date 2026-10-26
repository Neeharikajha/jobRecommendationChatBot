import logging
import re
from chat.models import Resume, Message, Application
from .matcher import search_jobs, get_job
from .llm import generate_text

log = logging.getLogger(__name__)

_SESSION_JOB_MAP  = "last_job_map"   # {display_num_str: real_job_id_int}
_SESSION_JOB_LIST = "last_job_list"  # [job_id, ...]
_SESSION_APP_MAP  = "last_app_map"   # {display_num_str: application_db_id}


# Intent classifier

def classify_intent(user_text: str) -> str:
    text = user_text.lower()

    # Check for remove / delete / withdraw requests first
    if any(w in text for w in ["remove", "withdraw", "delete", "cancel", "undo", "clear"]):
        if any(w in text for w in ["all", "everything", "history", "queue", "applied"]):
            return "remove_application"
        if any(c.isdigit() for c in user_text):
            return "remove_application"
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

    # Profile roles query check: e.g. "what roles would fit this job profile", "what roles suit me"
    if any(p in text for p in [
        "what roles", "which roles", "what jobs", "which jobs", "what position",
        "roles would fit", "roles will fit", "roles fit", "role fit", "roles suit",
        "fit this job profile", "fit my profile", "fit this profile",
        "what can i apply", "what should i apply", "roles can i apply",
        "suitable roles", "eligible for", "profile match",
        "based on my profile", "based on experience", "what am i eligible",
        "titles", "which title"
    ]):
        return "profile_roles"

    if any(w in text for w in [
        "search", "find", "show", "give", "get", "recommend", "suggest",
        "jobs", "job", "roles", "role", "doles", "dole", "position", "opportunities", "openings",
        "developer", "engineer", "frontend", "backend", "fullstack",
        "full stack", "frotned", "frotnend", "frontned", "remote", "python", "react", "java", "related to",
        "profile", "match", "more", "different"
    ]):
        if not any(w in text for w in ["applied", "application history"]):
            return "search_jobs"

    return "other"


# Helpers

def extract_display_ids(user_text: str) -> list[int]:
    text = re.sub(r'\s+and\s+', ', ', user_text.lower())
    text = re.sub(r'\s+or\s+', ', ', text)
    return [int(n) for n in re.findall(r'\d+', text)]


def extract_limit(user_text: str) -> int:
    text = user_text.lower()
    for pattern in [
        r'only\s+(\d+)',
        r'(\d+)\s+(?:jobs?|more|results?|positions?|roles?|doles?|opportunities?)',
        r'(?:give|show|find|search|suggest)\s+(?:me\s+)?(?:just\s+)?(?:only\s+)?(\d+)',
        r'(?:roles?|doles?|jobs?|please)[^\d]{1,10}(\d+)\b',
        r'\b(\d+)\s*$',
    ]:
        m = re.search(pattern, text)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 50:
                return val
    return 10


def extract_role_type(user_text: str) -> str | None:
    t = user_text.lower()
    words = re.findall(r'[a-z]+', t)

    detected: list[str] = []

    # Check for frontend (with typo tolerance e.g. frotned, frotnend, frontned, fontend)
    is_frontend = (
        any(k in t for k in ["frontend", "front end", "ui developer", "react developer", "front-end"])
        or any(w in ["frotned", "frotnend", "frontned", "fontend", "frntend", "frondend"] for w in words)
    )

    # Check for fullstack
    is_fullstack = (
        any(k in t for k in ["fullstack", "full stack", "full-stack"])
        or any(w in ["fulstack", "fullstck", "fullstak"] for w in words)
    )

    # Check for backend
    is_backend = (
        any(k in t for k in ["backend", "back end", "back-end"])
        or any(w in ["bakend", "backnd"] for w in words)
    )

    # Check for devops
    is_devops = (
        any(k in t for k in ["devops", "sre", "cloud engineer"])
    )

    # Check for data
    is_data = (
        any(k in t for k in ["data science", "machine learning", "ml engineer", "ai engineer"])
    )

    # Check for mobile
    is_mobile = (
        any(k in t for k in ["mobile", "android", "ios", "flutter", "react native"])
    )

    if is_frontend:
        detected.append("frontend")
    if is_fullstack:
        detected.append("fullstack")
    if is_backend:
        detected.append("backend")
    if is_devops:
        detected.append("devops")
    if is_data:
        detected.append("data")
    if is_mobile:
        detected.append("mobile")

    if detected:
        return ",".join(detected)
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


# Main agent

def run_agent(sid: str, user_text: str, request=None) -> dict:
    """
    Returns a dict:
      {
        "reply": str,
        "type": str,
        "jobs": list | None,
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

        # Apply to jobs
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
                        clean_title = j['title'].replace(" - ", " : ").replace("-", " ")
                        lines.append(f"  {j['display_id']}. {clean_title} at {j['company']} on {j['date']}")
                if already:
                    lines.append(f"Already applied to: {', '.join(map(str, already))}")
                if not_found:
                    lines.append(
                        f"Could not find job(s): {', '.join(map(str, not_found))}. "
                        "Search for jobs first, then use the numbers shown."
                    )
                result["reply"] = "\n".join(lines) or "No new applications made."

        # Remove / Clear applications
        elif intent == "remove_application":
            text_lower = user_text.lower()
            if any(w in text_lower for w in ["all", "everything", "history", "queue", "applied", "all jobs"]):
                deleted_count, _ = Application.objects.filter(session_key=sid).delete()
                if session is not None:
                    session[_SESSION_APP_MAP] = {}
                    session.modified = True
                result["reply"] = f"Removed all {deleted_count} job application(s) from your applied records."
            else:
                display_ids = extract_display_ids(user_text)
                if not display_ids:
                    result["reply"] = "Specify job numbers to remove, or say 'remove all jobs'. Example: 'remove 1, 2'"
                else:
                    # Get recent applications ordered as shown to the user
                    recent_apps = list(Application.objects.filter(session_key=sid).order_by("-applied_at"))
                    app_map = session.get(_SESSION_APP_MAP, {}) if session else {}

                    removed, not_applied = [], []
                    for d_id in display_ids:
                        app_to_delete = None
                        # Priority 1: Check by list position in last shown applications (1-indexed)
                        # Check session app map first if exists
                        if str(d_id) in app_map:
                            target_app_id = app_map[str(d_id)]
                            app_to_delete = Application.objects.filter(id=target_app_id, session_key=sid).first()

                        # Priority 2: 1-indexed position in current application history list
                        if not app_to_delete and 1 <= d_id <= len(recent_apps):
                            app_to_delete = recent_apps[d_id - 1]

                        # Priority 3: Fall back to job_id if matched from search job_map
                        if not app_to_delete:
                            real_job_id = job_map.get(str(d_id), d_id)
                            app_to_delete = Application.objects.filter(session_key=sid, job_id=real_job_id).first()

                        if app_to_delete:
                            clean_t = app_to_delete.job_title.replace(" - ", " : ").replace("-", " ")
                            removed.append(f"{clean_t} at {app_to_delete.company}")
                            app_to_delete.delete()
                        else:
                            not_applied.append(d_id)

                    lines = []
                    if removed:
                        lines.append(f"Removed {len(removed)} application(s):")
                        lines += [f"  * {r}" for r in removed]
                    if not_applied:
                        lines.append(f"Application number(s) not found: {', '.join(map(str, not_applied))}")
                    result["reply"] = "\n".join(lines) or "Nothing to remove."

        # View applications
        elif intent == "view_applications":
            apps = Application.objects.filter(session_key=sid).order_by("-applied_at")
            if not apps.exists():
                result["reply"] = "No applications yet. Find jobs and apply!"
            else:
                apps_list = list(apps[:20])
                if session is not None:
                    # Store 1-indexed mapping to application db ids
                    session[_SESSION_APP_MAP] = {str(i + 1): a.id for i, a in enumerate(apps_list)}
                    session.modified = True

                result["type"] = "applications"
                result["applications"] = [
                    {
                        "index": i + 1,
                        "title": a.job_title.replace(" - ", " : ").replace("-", " "),
                        "company": a.company,
                        "status": a.status,
                        "date": a.applied_at.strftime("%d %b %Y"),
                    }
                    for i, a in enumerate(apps_list)
                ]
                result["reply"] = f"You have {apps.count()} application(s) on record."

        # Profile roles
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
                    level = "Fresher or Intern"
                    base = ["Software Development Intern", "Graduate Engineer Trainee", "Junior Software Developer"]
                    if has_fe: base += ["Frontend Developer Intern", "Junior UI Developer", "React Developer Intern"]
                    if has_be: base += ["Backend Developer Intern", "Junior Python Developer"]
                    if has_fe and has_be: base += ["Full Stack Developer Intern"]
                elif exp <= 3:
                    level = "Junior"
                    base = ["Junior Software Developer", "Associate Software Engineer"]
                    if has_fe: base += ["Frontend Developer", "React Developer", "UI Developer"]
                    if has_be: base += ["Backend Developer", "Python Developer"]
                    if has_fe and has_be: base += ["Full Stack Developer"]
                elif exp <= 6:
                    level = "Mid level"
                    base = ["Software Engineer", "Software Developer"]
                    if has_fe: base += ["Frontend Developer", "UI Engineer"]
                    if has_be: base += ["Backend Developer", "API Developer"]
                    if has_fe and has_be: base += ["Full Stack Developer"]
                    if has_cloud: base += ["DevOps Engineer", "Cloud Engineer"]
                else:
                    level = "Senior"
                    base = ["Senior Software Engineer", "Technical Lead"]
                    if has_fe: base += ["Senior Frontend Developer", "Frontend Technical Lead"]
                    if has_be: base += ["Senior Backend Developer", "Backend Technical Lead"]
                    if has_cloud: base += ["Senior DevOps Engineer", "Platform Engineer"]

                seen, unique = set(), []
                for role in base:
                    if role not in seen:
                        seen.add(role)
                        unique.append(role)

                result["type"] = "roles"
                skills_display = ", ".join((resume_data.get("skills") or [])[:8])
                roles_str = "\n".join(f"  {i+1}. {r}" for i, r in enumerate(unique[:10]))
                result["reply"] = (
                    f"Based on {exp} year(s) of experience ({level} level), "
                    f"here are the recommended job profiles:\n\n"
                    f"{roles_str}\n\n"
                    f"Key skills detected: {skills_display}\n\n"
                    f"Try asking: 'give me 6 frontend jobs' or 'find full stack jobs'"
                )

        # Search jobs
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

                    # Clean any hyphens in job titles
                    for job in jobs:
                        if job.get("title"):
                            job["title"] = job["title"].replace(" - ", " : ").replace("-", " ")

                    # Sequential display map: 1, 2, 3 ... -> real job_id
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
                        f"Click any card to expand details. "
                        f"To apply, type: 'apply to {apply_hint}'"
                    )

        # Fallback / Question answering
        else:
            if not resume_data:
                result["reply"] = (
                    "Upload your resume using the paperclip button to get started.\n\n"
                    "I can help you find matching jobs, filter by role or skills, "
                    "apply to positions, and track your applications."
                )
            else:
                # Check if this is the very first interaction for this session
                user_msg_count = Message.objects.filter(session_key=sid, role="user").count()
                
                # If the user is asking a specific question (e.g. experience, skills, education, projects, etc.)
                system_instruction = (
                    "You are a concise AI career assistant. You are given a user's resume data. "
                    "Answer the user's specific question directly and highlight the main answer (e.g., '1.5 years of experience', or key skill names). "
                    "Keep your answer to 1 to 2 short sentences. Do NOT list the general menu of actions or help text. "
                    "Never use hyphens (use ':' or '/' instead). Do not use emojis."
                )
                prompt = f"Resume data:\n{resume_data}\n\nUser question:\n{user_text}"
                try:
                    answer = generate_text(prompt, system_instruction)
                    # Clean any accidental hyphens or emojis
                    answer = answer.replace(" - ", " : ").replace("-", " ")
                    result["reply"] = answer
                except Exception as ex:
                    log.error(f"Fallback LLM error: {ex}")
                    # Direct rule-based answer for common questions like experience
                    tl = user_text.lower()
                    if any(w in tl for w in ["exp", "experience", "how many years", "how long"]):
                        exp = resume_data.get("experience_years", 0)
                        result["reply"] = f"{exp} year(s) of professional experience."
                    elif any(w in tl for w in ["skill", "tech", "stack"]):
                        skills = ", ".join(resume_data.get("skills", []))
                        result["reply"] = f"Skills detected: {skills}"
                    else:
                        if user_msg_count <= 1:
                            name = resume_data.get("name", "")
                            greeting = f"Hi {name}! " if name else ""
                            result["reply"] = (
                                f"{greeting}Here is what I can do:\n\n"
                                "  Find jobs: 'Show me frontend developer jobs' or 'Find remote roles'\n"
                                "  Filter: 'Only remote' or 'Jobs needing Python'\n"
                                "  Suitable roles: 'What roles would fit this job profile?'\n"
                                "  Apply: 'Apply to jobs 1, 2, 3'\n"
                                "  Track: 'Show my applied jobs'\n"
                                "  Clear: 'Remove all jobs'"
                            )
                        else:
                            result["reply"] = "Could you please rephrase your request?"

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
