import requests

def fetch_workable_jobs(query: str) -> list:
    """
    Fetches remote tech jobs from RemoteOK.
    No API key needed. Replaces Workable.
    """
    url     = "https://remoteok.com/api"
    headers = {"User-Agent": "JobRadar/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data        = response.json()
        jobs        = []
        query_lower = query.lower()
        query_words = query_lower.split()

        # First item is metadata — skip it
        for job in data[1:]:
            title = job.get("position", "").lower()
            tags  = " ".join(job.get("tags", [])).lower()
            if any(word in title or word in tags for word in query_words):
                jobs.append({
                    "title":       job.get("position", ""),
                    "company":     job.get("company", ""),
                    "location":    "Remote",
                    "description": job.get("description", ""),
                    "url":         job.get("url", ""),
                    "salary":      job.get("salary", "Not specified") or "Not specified",
                    "job_type":    "Full-time",
                    "posted_at":   job.get("date", ""),
                    "source":      "RemoteOK",
                    "remote":      True
                })
        print(f"RemoteOK: fetched {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"RemoteOK error: {e}")
        return []