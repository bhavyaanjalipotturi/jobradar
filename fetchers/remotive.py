import requests

def fetch_remotive_jobs(query: str) -> list:
    """
    Fetches remote tech jobs from Remotive.
    No API key needed.
    """
    url = "https://remotive.com/api/remote-jobs"
    params = {"search": query, "limit": 100}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        jobs = []
        query_lower = query.lower()
        for job in data.get("jobs", []):
            title = job.get("title", "").lower()
            if query_lower in title:
                jobs.append({
                    "title":       job.get("title", ""),
                    "company":     job.get("company_name", ""),
                    "location":    "Remote",
                    "description": job.get("description", ""),
                    "url":         job.get("url", ""),
                    "salary":      job.get("salary", "Not specified"),
                    "job_type":    job.get("job_type", ""),
                    "posted_at":   job.get("publication_date", ""),
                    "source":      "Remotive",
                    "remote":      True
                })
        print(f"Remotive: fetched {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"Remotive error: {e}")
        return []