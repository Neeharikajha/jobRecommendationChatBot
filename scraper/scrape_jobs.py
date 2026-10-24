import json
import re
import time
from pathlib import Path

import pandas as pd
from jobspy import scrape_jobs

OUT = Path(__file__). resolve().parent.parent / "data" / "jobs.json"
TARGET = 1800
TERMS = ["python developer", "django developer", "react developer", "frontend developer",
         "backend developer", "full stack developer", "data analyst", "data scientist",
         "machine learning engineer", "ai engineer", "devops engineer", "java developer",
         "node.js developer", "software engineer", "qa engineer", "android developer",
         "flutter developer", "cloud engineer", "software engineer intern", "business analyst"]
SKILLS = ["python", "django", "flask", "fastapi", "javascript", "typescript", "react", "angular",
          "vue", "node.js", "express", "java", "spring", "c++", "c#", ".net", "go", "rust", "php",
          "laravel", "sql", "mysql", "postgresql", "mongodb", "redis", "aws", "azure", "gcp",
          "docker", "kubernetes", "git", "linux", "html", "css", "tailwind", "rest", "graphql",
          "machine learning", "deep learning", "nlp", "pandas", "numpy", "tensorflow", "pytorch",
          "langchain", "llm", "excel", "power bi", "tableau", "flutter", "kotlin", "swift",
          "selenium", "jenkins", "terraform", "kafka"]

def clean(v) -> str:
    return "" if pd.isna(v) else str(v).strip()

def find_skills(text: str) -> list[str]:
    return [s for s in SKILLS
            if re.search(r"(?<![\w+#.])" + re.escape(s) + r"(?![\w+#])", text, re.I)]

def find_exp(text: str):
    m = re.search(r"(\d+)\s*(?:-|to|–)?\s*(\d+)?\+?\s*(?:years|yrs|year)", text, re.I)
    if not m:
        return 0, "Not specified"
    lo, hi = int(m.group(1)), m.group(2)
    return lo, (f"{lo}-{hi} years" if hi else f"{lo}+ years")

def main():
    jobs, seen = [], set()
    for term in TERMS:
        if len(jobs) >= TARGET:
            break
        print(f"Scraping: {term} (have {len(jobs)})")
        try:
            df = scrape_jobs(site_name=["indeed", "linkedin"], search_term=term,
                             location="India", country_indeed="India",
                             results_wanted=120, hours_old=720,
                             linkedin_fetch_description=True)
        except Exception as e:
            print("  failed:", e)
            continue
        for _, r in df.iterrows():
            url = clean(r.get("job_url"))
            if not url or url in seen:
                continue
            seen.add(url)
            desc = clean(r.get("description"))
            title, loc = clean(r.get("title")), clean(r.get("location"))
            exp_min, exp_text = find_exp(desc)
            remote = (r.get("is_remote") is True) or "remote" in f"{title} {loc} {desc[:300]}".lower()
            jobs.append({
                "job_id": len(jobs) + 1,
                "title": title,
                "company": clean(r.get("company")),
                "location": loc,
                "remote": bool(remote),
                "experience_required": exp_text,
                "exp_min": exp_min,
                "skills": find_skills(f"{title} {desc}"),
                "description": desc[:1500],
                "source_link": url,
            })
        time.sleep(3)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(jobs, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(jobs)} jobs → {OUT}")

if __name__ == "__main__":
    main()