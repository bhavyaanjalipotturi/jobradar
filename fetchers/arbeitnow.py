import requests

def fetch_arbeitnow_jobs(query: str) -> list:
    """
    Fetches global tech jobs from Arbeitnow.
    No API key needed. Updated hourly.
    """
    url = "https://www.arbeitnow.com/api/job-board-api"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        jobs = []
        query_lower = query.lower()
        for job in data.get("data", []):
            title = job.get("title", "").lower()
            if query_lower in title:
                jobs.append({
                    "title":       job.get("title", ""),
                    "company":     job.get("company_name", ""),
                    "location":    job.get("location", ""),
                    "description": job.get("description", ""),
                    "url":         job.get("url", ""),
                    "salary":      "Not specified",
                    "job_type":    "Full-time",
                    "posted_at":   str(job.get("created_at", "")),
                    "source":      "Arbeitnow",
                    "remote":      job.get("remote", False)
                })
        print(f"Arbeitnow: fetched {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"Arbeitnow error: {e}")
        return []