import requests

def fetch_themuse_jobs(query: str) -> list:
    url = "https://www.themuse.com/api/public/jobs"
    params = {
        "descending": "true",
        "page":       1
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        jobs = []
        query_words = query.lower().split()
        for job in data.get("results", []):
            title = job.get("name", "").lower()
            if any(word in title for word in query_words):
                locations = job.get("locations", [])
                location  = locations[0].get("name", "USA") if locations else "USA"
                jobs.append({
                    "title":       job.get("name", ""),
                    "company":     job.get("company", {}).get("name", ""),
                    "location":    location,
                    "description": job.get("contents", ""),
                    "url":         job.get("refs", {}).get("landing_page", ""),
                    "salary":      "Not specified",
                    "job_type":    "Full-time",
                    "posted_at":   job.get("publication_date", ""),
                    "source":      "The Muse",
                    "remote":      False
                })
        print(f"The Muse: fetched {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"The Muse error: {e}")
        return []