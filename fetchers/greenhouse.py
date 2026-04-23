import requests

GREENHOUSE_COMPANIES = [
    "anthropic", "notion", "airtable", "figma",
    "stripe", "databricks", "scale", "huggingface",
    "retool", "vercel", "planetscale", "dbt-labs",
    "openai", "cohere", "modal-labs", "replit"
]

def fetch_greenhouse_jobs(query: str) -> list:
    jobs = []
    query_words = query.lower().split()
    for company in GREENHOUSE_COMPANIES:
        try:
            url      = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            for job in data.get("jobs", []):
                title = job.get("title", "").lower()
                if any(word in title for word in query_words):
                    jobs.append({
                        "title":       job.get("title", ""),
                        "company":     company.replace("-", " ").title(),
                        "location":    job.get("location", {}).get("name", ""),
                        "description": job.get("content", ""),
                        "url":         job.get("absolute_url", ""),
                        "salary":      "Not specified",
                        "job_type":    "Full-time",
                        "posted_at":   job.get("updated_at", ""),
                        "source":      "Greenhouse",
                        "remote":      "remote" in job.get("location", {}).get("name", "").lower()
                    })
        except Exception:
            continue
    print(f"Greenhouse: fetched {len(jobs)} jobs")
    return jobs