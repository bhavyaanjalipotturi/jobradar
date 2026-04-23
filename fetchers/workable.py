import requests

def fetch_workable_jobs(query: str) -> list:
    """
    Fetches jobs from small/medium businesses via Workable.
    No API key needed.
    """
    url = "https://www.workable.com/api/jobs"
    params = {"query": query, "limit": 50}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        jobs = []
        for job in data.get("results", []):
            jobs.append({
                "title":       job.get("title", ""),
                "company":     job.get("company", {}).get("name", ""),
                "location":    job.get("location", {}).get("city", ""),
                "description": job.get("description", ""),
                "url":         job.get("url", ""),
                "salary":      "Not specified",
                "job_type":    job.get("employment_type", ""),
                "posted_at":   job.get("published_on", ""),
                "source":      "Workable",
                "remote":      job.get("remote", False)
            })
        print(f"Workable: fetched {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"Workable error: {e}")
        return []