import json
import re
from functools import lru_cache
from pathlib import Path
from django.conf import settings
from rapidfuzz import fuzz

@lru_cache(maxsize=1)
def load_jobs() -> list[dict]:
    """Load jobs from JSON file."""
    return json.loads(Path(settings.BASE_DIR, "data", "jobs.json").read_text(encoding="utf-8"))

def get_job(job_id: int) -> dict:
    """Get a single job by its real job_id."""
    jobs = load_jobs()
    for job in jobs:
        jid = job.get("job_id") or job.get("id")
        if jid == job_id:
            return job
    return None

def _extract_min_years(exp_string) -> int:
    """Extract minimum experience years from string like '5-3 years' or '0'."""
    if isinstance(exp_string, (int, float)):
        return int(exp_string)
    if not exp_string:
        return 0
    exp_string = str(exp_string).lower()
    exp_string = exp_string.replace("years", "").replace("+", "").replace("yrs", "").strip()
    if not exp_string or "not specified" in exp_string or exp_string == "-":
        return 0
    # Get first number from string
    nums = re.findall(r'\d+', exp_string)
    return int(nums[0]) if nums else 0

def _is_senior_role(title: str) -> bool:
    """Check if the job title indicates a senior/lead/principal level."""
    title_lower = (title or "").lower()
    senior_markers = [
        "senior", "sr.", "sr ", "lead", "principal", "staff", "architect",
        "head of", "manager", "director", "vp ", "vice president", "chief"
    ]
    return any(m in title_lower for m in senior_markers)

def _is_intern_role(title: str) -> bool:
    """Check if the job title is an internship."""
    title_lower = (title or "").lower()
    return any(m in title_lower for m in ["intern", "internship", "trainee"])

def _get_role_type(title: str) -> str:
    """Classify a job title into a broad role category."""
    title_lower = (title or "").lower()
    if any(k in title_lower for k in ["frontend", "front-end", "front end", "ui developer", "react developer", "angular", "vue"]):
        return "frontend"
    if any(k in title_lower for k in ["backend", "back-end", "back end", "api developer", "django", "fastapi", "node.js developer"]):
        return "backend"
    if any(k in title_lower for k in ["full stack", "fullstack", "full-stack"]):
        return "fullstack"
    if any(k in title_lower for k in ["devops", "sre", "infrastructure", "cloud engineer"]):
        return "devops"
    if any(k in title_lower for k in ["data", "ml ", "machine learning", "ai ", "artificial intelligence", "data science"]):
        return "data"
    if any(k in title_lower for k in ["mobile", "android", "ios", "flutter", "react native"]):
        return "mobile"
    return "other"


def search_jobs(
    resume: dict,
    remote: bool = None,
    skills: list = None,
    location: str = None,
    keyword: str = None,
    role_type: str = None,
    limit: int = 10,
    exp_filter: bool = True
) -> dict:
    """
    Search jobs matching resume skills/experience, with optional filters.
    Returns list of best matches with match_reason and full details.
    
    - exp_filter: if True, respect user's experience level (exclude senior roles for freshers/juniors)
    - role_type: "frontend", "backend", "fullstack", "devops", etc.
    """
    jobs = load_jobs()

    resume_exp = resume.get("experience_years", 0)
    if not isinstance(resume_exp, (int, float)):
        resume_exp = _extract_min_years(resume_exp)
    resume_exp = int(resume_exp)

    # Determine user seniority thresholds
    # 0-1 yrs: fresher/intern, 1-3: junior, 3-6: mid, 6+: senior
    is_fresher = resume_exp <= 1
    is_junior = resume_exp <= 3

    scored = []
    for job in jobs:
        score = 0
        reasons = []

        job_title = (job.get("title") or "")
        job_title_lower = job_title.lower()

        # ── Experience-level gate ──────────────────────────────────────────
        if exp_filter:
            job_exp_req = _extract_min_years(job.get("experience_required") or job.get("exp_min", 0))

            # Don't recommend senior roles to freshers/juniors
            if is_junior and _is_senior_role(job_title):
                continue

            # Freshers shouldn't see roles requiring 3+ years
            if is_fresher and job_exp_req > 2:
                continue

            # Don't recommend intern roles to experienced candidates (>2 yrs)
            if resume_exp > 2 and _is_intern_role(job_title):
                continue

        # ── Skill matching ─────────────────────────────────────────────────
        resume_skills = set(s.lower() for s in (resume.get("skills") or []))
        job_skills = set(s.lower() for s in (job.get("skills") or []))
        skill_matches = resume_skills & job_skills
        if skill_matches:
            score += len(skill_matches) * 20
            reasons.append(f"{len(skill_matches)} skills match")

        # ── Experience score ───────────────────────────────────────────────
        job_exp_req = _extract_min_years(job.get("experience_required") or job.get("exp_min", 0))
        if resume_exp >= job_exp_req:
            score += 30
            reasons.append("experience fits")
        elif resume_exp >= job_exp_req * 0.7:
            score += 15
            reasons.append("slightly junior")

        # ── Designation / role title matching ─────────────────────────────
        resume_desig = (resume.get("designation") or "").lower()
        if resume_desig and job_title_lower:
            similarity = fuzz.token_sort_ratio(resume_desig, job_title_lower)
            if similarity > 65:
                score += similarity // 10
                reasons.append("role similar")

        # ── Remote filter ─────────────────────────────────────────────────
        if remote is not None and job.get("remote") != remote:
            continue

        # ── Location filter ───────────────────────────────────────────────
        if location and location.lower() not in (job.get("location") or "").lower():
            continue

        # ── Role type filter ──────────────────────────────────────────────
        if role_type:
            rt = role_type.lower()
            job_rt = _get_role_type(job_title)
            # Also check job skills for role-type signals
            skill_set = " ".join(job.get("skills") or []).lower()
            rt_matched = False
            if rt == "frontend":
                rt_matched = (job_rt == "frontend" or
                              any(k in job_title_lower for k in ["frontend", "front-end", "front end", "react", "angular", "vue"]) or
                              any(k in skill_set for k in ["react", "angular", "vue", "html", "css", "javascript", "typescript", "next.js", "gatsby"]))
            elif rt == "backend":
                rt_matched = (job_rt == "backend" or
                              any(k in job_title_lower for k in ["backend", "back-end", "back end", "api"]) or
                              any(k in skill_set for k in ["django", "fastapi", "express", "spring", "rails", "golang", "rust", "node"]))
            elif rt == "fullstack":
                rt_matched = (job_rt == "fullstack" or
                              any(k in job_title_lower for k in ["fullstack", "full stack", "full-stack"]))
            elif rt == "devops":
                rt_matched = (job_rt == "devops" or
                              any(k in job_title_lower for k in ["devops", "sre", "cloud", "infrastructure"]))
            else:
                rt_matched = rt in job_title_lower or rt in skill_set
            if not rt_matched:
                continue

        # ── Skills filter (from user query like "jobs needing React") ──────
        if skills:
            filter_skills_lower = set(s.lower() for s in skills)
            job_skills_lower = set(s.lower() for s in (job.get("skills") or []))
            skill_match_found = any(
                s in job_skills_lower or s in job_title_lower
                for s in filter_skills_lower
            )
            if not skill_match_found:
                continue

        # ── Keyword filter ─────────────────────────────────────────────────
        if keyword:
            kw = keyword.lower()
            if kw not in job_title_lower and kw not in (job.get("description") or "").lower():
                continue

        if score > 0 or not (remote is not None or location or skills or keyword or role_type):
            scored.append((score, job, reasons))

    # Sort by score descending
    scored.sort(reverse=True, key=lambda x: x[0])
    top = scored[:limit]

    return {
        "count": len(top),
        "jobs": [
            {
                "job_id": job.get("job_id") or job.get("id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "experience_required": job.get("experience_required") or job.get("exp_min", "Not specified"),
                "remote": job.get("remote"),
                "skills": job.get("skills", []),
                "description_snippet": (job.get("description") or "")[:200].strip(),
                "match_reason": " + ".join(reasons) if reasons else "matches your profile",
                "source_link": job.get("source_link") or "",
            }
            for score, job, reasons in top
        ]
    }
