import json
import logging
import re
from datetime import datetime
from chat.models import Resume, Message, Application
from .matcher import search_jobs, get_job

log = logging.getLogger(__name__)

# ─── SESSION KEYS ────────────────────────────────────────────────────────────
_SESSION_JOB_MAP = "last_job_map"      # {display_num_str: real_job_id}
_SESSION_JOB_LIST = "last_job_list"    # full job dicts for last search


# ─── INTENT CLASSIFIER ───────────────────────────────────────────────────────

def classify_intent(user_text: str) -> str:
    """Classify user intent using keywords."""
    text_lower = user_text.lower()

    # Remove / Withdraw
    if any(w in text_lower for w in ["remove", "withdraw", "delete", "cancel", "undo"]):
        if any(c.isdigit() for c in user_text):
            return "remove_application"

    # Apply
    if any(w in text_lower for w in ["apply to", "apply for", "apply job", "submit application", "apply"]):
        if any(c.isdigit() for c in user_text):
            return "apply_jobs"

    # View applications
    if any(w in text_lower for w in ["applied", "applications", "my applications", "application history",
                                      "where have i applied", "which jobs have i", "show applied"]):
        return "view_applications"

    # Roles from profile
    if any(phrase in text_lower for phrase in [
        "what roles", "which roles", "what jobs", "which jobs", "what position",
        "what can i apply", "what should i apply", "roles can i apply",
        "titles", "suitable roles", "eligible for", "profile match",
        "based on my profile", "based on experience", "what am i eligible"
    ]):
        return "profile_roles"

    # Search / Find
    if any(w in text_lower for w in [
        "search", "find", "show", "give", "get", "recommend", "match",
        "jobs", "roles", "position", "opportunities", "openings",
        "developer", "engineer", "frontend", "backend", "fullstack",
        "full stack", "remote", "python", "react", "java", "related to", "profile"
    ]):
        if not any(w in text_lower for w in ["applied", "application history"]):
            return "search_jobs"

    return "other"


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def extract_display_ids(user_text: str) -> list[int]:
    """Extract display numbers from user text ('apply to 1, 2, 3' → [1, 2, 3])."""
    text = re.sub(r'\s+and\s+', ', ', user_text.lower())
    text = re.sub(r'\s+or\s+', ', ', text)
    return [int(n) for n in re.findall(r'\d+', text)]


def extract_limit(user_text: str) -> int:
    """Extract desired number of jobs from text (e.g., 'only 7', '5 jobs')."""
    text = user_text.lower()
    m = re.search(r'only\s+(\d+)', text)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)\s+(?:jobs?|more|results?|positions?|roles?|opportunities?)', text)
    if m:
        return int(m.group(1))
    m = re.search(r'(?:give|show|find|search)\s+(?:me\s+)?(\d+)', text)
    if m:
        return int(m.group(1))
    return 10


def extract_role_type(user_text: str) -> str | None:
    """Detect role type (frontend/backend/fullstack/etc.) from user text."""
    text_lower = user_text.lower()
    if any(k in text_lower for k in ["frontend", "front-end", "front end", "react developer", "ui developer"]):
        return "frontend"
    if any(k in text_lower for k in ["backend", "back-end", "back end"]):
        return "backend"
    if any(k in text_lower for k in ["fullstack", "full stack", "full-stack"]):
        return "fullstack"
    if any(k in text_lower for k in ["devops", "sre", "cloud engineer"]):
        return "devops"
    if any(k in text_lower for k in ["data science", "machine learning", "ml engineer", "ai engineer"]):
        return "data"
    if any(k in text_lower for k in ["mobile", "android", "ios", "flutter"]):
        return "mobile"
    return None


def extract_skills_filter(user_text: str) -> list | None:
    """Extract explicit skill mentions like 'jobs needing React'."""
    text_lower = user_text.lower()
    known_skills = [
        "react", "angular", "vue", "javascript", "typescript", "html", "css",
        "python", "java", "node", "express", "django", "fastapi", "spring",
        "aws", "azure", "gcp", "docker", "kubernetes", "postgres", "mysql",
        "mongodb", "golang", "rust", "flutter", "kotlin", "swift",
    ]
    found = [s for s in known_skills if re.search(rf'\b{re.escape(s)}\b', text_lower)]
    return found if found else None


def format_job_card(display_num: int, job: dict) -> str:
    """Format a job as a readable card with all key details."""
    link = job.get("source_link", "")
    link_text = f"\n   🔗 Apply: {link}" if link else ""
    snippet = job.get("description_snippet", "")
    snippet_text = f"\n   📄 {snippet}..." if snippet else ""
    exp = job.get("experience_required", "Not specified")
    skills = ", ".join((job.get("skills") or [])[:6])
    remote_badge = " 🌐 Remote" if job.get("remote") else ""
    return (
        f"**{display_num}. {job['title']}** at {job['company']}{remote_badge}\n"
        f"   📍 {job['location']}\n"
        f"   🏷️ Experience: {exp}\n"
        f"   ✅ Match: {job['match_reason']}\n"
        f"   🔧 Skills: {skills}"
        f"{snippet_text}"
        f"{link_text}"
    )


# ─── MAIN AGENT ──────────────────────────────────────────────────────────────

def run_agent(sid: str, user_text: str, request=None) -> str:
    """
    Run the job assistant agent.
    - sid: session key (string)
    - request: Django request (optional, used to store/retrieve session job maps)
    """
    try:
        r = Resume.objects.filter(session_key=sid).first()
        resume_data = r.data if r else {}

        intent = classify_intent(user_text)
        log.info(f"Intent: {intent!r} | Message: {user_text[:60]}")

        # ── RETRIEVE last job map from session ────────────────────────────
        # display_num → real job_id (both stored as str keys in session JSON)
        session = request.session if request else None
        job_map: dict = {}  # {display_str: real_job_id_int}
        if session:
            raw = session.get(_SESSION_JOB_MAP, {})
            job_map = {str(k): int(v) for k, v in raw.items()} if raw else {}

        # ── APPLY TO JOBS ─────────────────────────────────────────────────
        if intent == "apply_jobs":
            display_ids = extract_display_ids(user_text)
            if not display_ids:
                reply = "I didn't find any job numbers. Try 'apply to job 1' or 'apply to jobs 1, 2, 3'"
            else:
                applied_jobs = []
                already_applied = []
                not_found = []

                for display_id in display_ids:
                    # Map display number → real job_id
                    real_job_id = job_map.get(str(display_id))
                    if real_job_id is None:
                        # Fallback: try treating display_id as real job_id
                        job = get_job(display_id)
                        if job:
                            real_job_id = display_id
                        else:
                            not_found.append(display_id)
                            continue
                    else:
                        job = get_job(real_job_id)
                        if not job:
                            not_found.append(display_id)
                            continue

                    app, created = Application.objects.get_or_create(
                        session_key=sid,
                        job_id=real_job_id,
                        defaults={
                            "job_title": job.get("title", ""),
                            "company": job.get("company", "")
                        }
                    )
                    if created:
                        applied_jobs.append({
                            "title": job.get("title", ""),
                            "company": job.get("company", ""),
                            "link": job.get("source_link", ""),
                            "date": app.applied_at.strftime('%d %b %Y')
                        })
                    else:
                        already_applied.append(display_id)

                if applied_jobs:
                    job_list = "\n".join([
                        f"✅ **{j['title']}** at {j['company']} (applied {j['date']})"
                        + (f"\n   🔗 {j['link']}" if j['link'] else "")
                        for j in applied_jobs
                    ])
                    reply = f"Applied to {len(applied_jobs)} job(s):\n\n{job_list}"
                    if already_applied:
                        reply += f"\n\n⚠️ Already applied: {', '.join(map(str, already_applied))}"
                    if not_found:
                        reply += f"\n\n❌ Not found: {', '.join(map(str, not_found))} — search for jobs first!"
                else:
                    if already_applied:
                        reply = f"You've already applied to job(s): {', '.join(map(str, already_applied))}"
                    elif not_found:
                        reply = (f"Job number(s) {', '.join(map(str, not_found))} not found in the last search. "
                                 f"Search for jobs first, then apply by the number shown.")
                    else:
                        reply = "No new applications made."

        # ── REMOVE APPLICATION ────────────────────────────────────────────
        elif intent == "remove_application":
            display_ids = extract_display_ids(user_text)
            if not display_ids:
                reply = "I didn't find any job numbers to remove. Try 'remove job 1' or 'withdraw from 1, 2'"
            else:
                removed = []
                not_applied = []
                not_found_ids = []

                for display_id in display_ids:
                    real_job_id = job_map.get(str(display_id), display_id)
                    try:
                        app = Application.objects.get(session_key=sid, job_id=real_job_id)
                        removed.append({"title": app.job_title, "company": app.company})
                        app.delete()
                    except Application.DoesNotExist:
                        if get_job(real_job_id):
                            not_applied.append(display_id)
                        else:
                            not_found_ids.append(display_id)

                if removed:
                    job_list = "\n".join([f"❌ {j['title']} at {j['company']}" for j in removed])
                    reply = f"Removed {len(removed)} application(s):\n{job_list}"
                    if not_applied:
                        reply += f"\n\n⚠️ You hadn't applied to: {', '.join(map(str, not_applied))}"
                else:
                    if not_applied:
                        reply = f"You haven't applied to: {', '.join(map(str, not_applied))}"
                    elif not_found_ids:
                        reply = f"Job numbers not found: {', '.join(map(str, not_found_ids))}"
                    else:
                        reply = "No applications to remove."

        # ── VIEW APPLICATIONS ─────────────────────────────────────────────
        elif intent == "view_applications":
            apps = Application.objects.filter(session_key=sid).order_by("-applied_at")
            if not apps.exists():
                reply = "No applications yet. Search for jobs and apply!"
            else:
                lines = [
                    f"{i+1}. **{a.job_title}** at {a.company} — {a.status} ({a.applied_at.strftime('%d %b %Y')})"
                    for i, a in enumerate(apps[:15])
                ]
                reply = f"Your applications ({apps.count()}):\n\n" + "\n".join(lines)

        # ── PROFILE-BASED ROLE SUGGESTIONS ───────────────────────────────
        elif intent == "profile_roles":
            if not resume_data:
                reply = "Please upload your resume first so I can suggest suitable roles."
            else:
                exp = resume_data.get("experience_years", 0)
                skills = resume_data.get("skills", [])
                desig = resume_data.get("designation", "")
                skills_lower = [s.lower() for s in skills]

                suggested = []

                # Fresher / Intern (0-1 yr)
                if exp <= 1:
                    level = "fresher / intern"
                    suggested += ["Software Development Intern", "Junior Software Developer", "Graduate Trainee"]
                    if any(s in skills_lower for s in ["react", "angular", "vue", "html", "css", "javascript", "typescript"]):
                        suggested += ["Frontend Developer Intern", "Junior UI Developer", "React Developer Intern"]
                    if any(s in skills_lower for s in ["python", "django", "fastapi", "node", "java"]):
                        suggested += ["Backend Developer Intern", "Junior Backend Developer"]
                    if any(s in skills_lower for s in ["react", "node", "python"]):
                        suggested += ["Full Stack Developer Intern"]

                # Junior (1-3 yrs)
                elif exp <= 3:
                    level = "junior"
                    suggested += ["Junior Software Developer", "Associate Software Engineer", "Engineer Trainee"]
                    if any(s in skills_lower for s in ["react", "angular", "vue", "html", "css", "javascript", "typescript"]):
                        suggested += ["Junior Frontend Developer", "Frontend Developer", "React Developer", "UI Developer"]
                    if any(s in skills_lower for s in ["python", "django", "fastapi", "node", "java", "spring"]):
                        suggested += ["Junior Backend Developer", "Backend Developer", "Python Developer", "Node.js Developer"]
                    if any(s in skills_lower for s in ["react", "node", "python", "django"]):
                        suggested += ["Junior Full Stack Developer", "Full Stack Developer"]

                # Mid-level (3-6 yrs)
                elif exp <= 6:
                    level = "mid-level"
                    suggested += ["Software Developer", "Software Engineer", "Full Stack Developer"]
                    if any(s in skills_lower for s in ["react", "angular", "vue", "javascript", "typescript"]):
                        suggested += ["Frontend Developer", "React Developer", "UI Engineer"]
                    if any(s in skills_lower for s in ["python", "django", "fastapi", "node", "java"]):
                        suggested += ["Backend Developer", "Python Developer", "API Developer"]
                    if any(s in skills_lower for s in ["aws", "docker", "kubernetes", "gcp", "azure"]):
                        suggested += ["DevOps Engineer", "Cloud Engineer", "Platform Engineer"]

                # Senior (6+ yrs)
                else:
                    level = "senior"
                    suggested += ["Senior Software Engineer", "Senior Developer", "Tech Lead", "Software Architect"]
                    if any(s in skills_lower for s in ["react", "angular", "vue", "javascript", "typescript"]):
                        suggested += ["Senior Frontend Developer", "Senior UI Engineer", "Frontend Tech Lead"]
                    if any(s in skills_lower for s in ["python", "django", "fastapi", "node", "java"]):
                        suggested += ["Senior Backend Developer", "Backend Tech Lead", "Senior Python Developer"]

                # Deduplicate
                seen = set()
                unique = []
                for r in suggested:
                    if r not in seen:
                        seen.add(r)
                        unique.append(r)

                roles_list = "\n".join(f"  • {r}" for r in unique[:15])
                reply = (
                    f"Based on your profile ({exp} yrs experience, {level} level), "
                    f"here are suitable roles you can apply for:\n\n"
                    f"{roles_list}\n\n"
                    f"_Skills detected: {', '.join(skills[:8])}_\n\n"
                    f"Type **'find me frontend jobs'** or **'show full stack roles'** to search!"
                )

        # ── SEARCH JOBS ───────────────────────────────────────────────────
        elif intent == "search_jobs":
            if not resume_data:
                reply = "Please upload your resume first so I can find matching jobs!"
            else:
                remote_only = "remote" in user_text.lower()
                limit = extract_limit(user_text)
                role_type = extract_role_type(user_text)
                skills_filter = extract_skills_filter(user_text)

                # If role_type detected, don't also pass it as a plain skill
                if role_type and skills_filter:
                    # Remove category keywords from skills_filter
                    role_kws = {"frontend", "backend", "fullstack", "full stack", "full-stack",
                                "devops", "mobile", "android", "ios"}
                    skills_filter = [s for s in skills_filter if s not in role_kws] or None

                log.info(f"Search: remote={remote_only}, role_type={role_type}, skills={skills_filter}, limit={limit}")

                results = search_jobs(
                    resume_data,
                    remote=remote_only if remote_only else None,
                    skills=skills_filter,
                    role_type=role_type,
                    limit=limit,
                    exp_filter=True,
                )

                if results["count"] == 0:
                    filter_desc = role_type or (skills_filter[0] if skills_filter else "matching")
                    reply = (
                        f"No {filter_desc} jobs found matching your profile. "
                        f"Try broader keywords, e.g. 'show me developer jobs' or 'find remote jobs'."
                    )
                else:
                    jobs = results["jobs"]

                    # Build sequential display mapping and save to session
                    new_map = {}
                    for idx, job in enumerate(jobs, start=1):
                        new_map[str(idx)] = job["job_id"]

                    if session is not None:
                        session[_SESSION_JOB_MAP] = new_map
                        session[_SESSION_JOB_LIST] = [j["job_id"] for j in jobs]
                        session.modified = True

                    # Format cards
                    cards = "\n\n".join(format_job_card(idx, job) for idx, job in enumerate(jobs, start=1))

                    apply_hint = ", ".join(str(i) for i in range(1, min(4, len(jobs) + 1)))
                    reply = (
                        f"Found **{results['count']}** matching jobs:\n\n"
                        f"{cards}\n\n"
                        f"💬 Type **'apply to {apply_hint}'** to apply, or refine: "
                        f"'show only remote', 'only frontend', 'jobs needing React', etc."
                    )

        # ── OTHER / FALLBACK ──────────────────────────────────────────────
        else:
            if not resume_data:
                reply = (
                    "Hi! Please upload your resume (📎 button) so I can find matching jobs for you.\n\n"
                    "I can help you:\n"
                    "• **Find jobs**: 'Show me frontend developer jobs'\n"
                    "• **Filter**: 'Only remote roles' or 'Jobs needing React'\n"
                    "• **Apply**: 'Apply to jobs 1, 2, 3'\n"
                    "• **Check applications**: 'Show my applied jobs'\n"
                    "• **Know suitable roles**: 'What roles can I apply to?'"
                )
            else:
                exp = resume_data.get("experience_years", 0)
                name = resume_data.get("name", "there")
                reply = (
                    f"Hi {name}! I can help you:\n\n"
                    f"• **Find jobs**: 'Show me developer jobs' or 'Find remote frontend roles'\n"
                    f"• **Filter**: 'Only 7 jobs' or 'Jobs needing Python'\n"
                    f"• **Profile roles**: 'What roles can I apply to?'\n"
                    f"• **Apply**: 'Apply to jobs 1, 2, 3'\n"
                    f"• **Applications**: 'Show my applied jobs'\n\n"
                    f"_Your profile: {exp} yrs experience. Skills: {', '.join((resume_data.get('skills') or [])[:5])}_"
                )

    except Exception as e:
        log.exception(f"Agent error: {e}")
        reply = "Something went wrong. Please try again."

    # Save messages
    try:
        Message.objects.create(session_key=sid, role="user", content=user_text)
        Message.objects.create(session_key=sid, role="model", content=reply)
    except Exception as e:
        log.error(f"Failed to save messages: {e}")

    return reply
