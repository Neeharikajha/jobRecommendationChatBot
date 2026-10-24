import json
from functools import lru_cache
from pathlib import Path
from django.conf import settings
from rapidfuzz import fuzz

@lru_cache(maxsize=1)
def load_jobs() -> list[dict]:
    """Load jobs from JSON file."""
    return json.loads(Path(settings.BASE_DIR, "data", "jobs.json").read_text(encoding="utf-8"))

def get_job(job_id: int) -> dict:
    """Get a single job by ID."""
    jobs = load_jobs()
    for job in jobs:
        # Handle both 'id' and 'job_id' keys
        job_key_id = job.get("id") or job.get("job_id")
        if job_key_id == job_id:
            return job
    return None

def _extract_min_years(exp_string: str) -> int:
    """Extract minimum experience years from string like '5-3 years' or '0'."""
    if isinstance(exp_string, int):
        return exp_string
    if not exp_string:
        return 0
    # Handle strings like "5-3 years", "Not specified", "3+ years", etc.
    exp_string = str(exp_string).lower().replace("years", "").replace("+", "").strip()
    if not exp_string or exp_string == "not specified":
        return 0
    # Get first number from string
    for char in exp_string:
        if char.isdigit():
            # Collect all consecutive digits
            num = ""
            idx = exp_string.index(char)
            for c in exp_string[idx:]:
                if c.isdigit():
                    num += c
                else:
                    break
            return int(num) if num else 0
    return 0

def search_jobs(resume: dict, remote: bool = None, skills: list = None, location: str = None, 
                keyword: str = None, limit: int = 10) -> dict:
    """
    Search jobs matching resume skills/experience, with optional filters.
    Returns list of best matches with match_reason and basic info.
    """
    jobs = load_jobs()
    
    # Score each job
    scored = []
    for job in jobs:
        score = 0
        reasons = []
        
        # Skill matching
        resume_skills = set(s.lower() for s in (resume.get("skills") or []))
        job_skills = set(s.lower() for s in (job.get("skills") or []))
        skill_matches = resume_skills & job_skills
        if skill_matches:
            score += len(skill_matches) * 20
            reasons.append(f"{len(skill_matches)} skills match")
        
        # Experience matching
        resume_exp = resume.get("experience_years", 0)
        if not isinstance(resume_exp, int):
            resume_exp = _extract_min_years(resume_exp)
        
        job_exp_required = job.get("experience_required") or job.get("exp_min", 0)
        job_exp_required = _extract_min_years(job_exp_required)
        
        if resume_exp >= job_exp_required:
            score += 30
            reasons.append("experience fits")
        elif resume_exp >= job_exp_required * 0.7:
            score += 15
            reasons.append("slightly junior")
        
        # Designation/role matching
        resume_desig = (resume.get("designation") or "").lower()
        job_title = (job.get("title") or "").lower()
        if resume_desig and job_title:
            similarity = fuzz.token_sort_ratio(resume_desig, job_title)
            if similarity > 70:
                score += similarity // 10
                reasons.append(f"role similar")
        
        # Apply filters
        if remote is not None and job.get("remote") != remote:
            continue
        if location and location.lower() not in (job.get("location") or "").lower():
            continue
        if skills:
            filter_skills = set(s.lower() for s in skills)
            if not filter_skills.issubset(job_skills):
                continue
        if keyword and keyword.lower() not in job_title and keyword.lower() not in (job.get("description") or "").lower():
            continue
        
        if score > 0 or not (remote is not None or location or skills or keyword):
            scored.append((score, job, reasons))
    
    # Sort by score and return top N
    scored.sort(reverse=True, key=lambda x: x[0])
    return {
        "count": len(scored[:limit]),
        "jobs": [
            {
                "id": job.get("id") or job.get("job_id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "experience_required": job.get("experience_required") or job.get("exp_min", 0),
                "remote": job.get("remote"),
                "match_reason": " + ".join(reasons) if reasons else "matches your profile",
                "source_link": job.get("source_link")
            }
            for score, job, reasons in scored[:limit]
        ]
    }
