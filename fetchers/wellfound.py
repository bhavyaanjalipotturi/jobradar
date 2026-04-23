import requests

def fetch_wellfound_jobs(query: str) -> list:
    """
    Fetches startup jobs from WellFound (AngelList).
    No API key needed.
    """
    url = "https://wellfound.com/api/graphql"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": """
        {
          startupSearchResults(query: \"""" + query + """\") {
            startups {
              name
              jobs {
                title
                locationNames
                description
                applyUrl
                jobType
              }
            }
          }
        }
        """
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        jobs = []
        if response.status_code == 200:
            data = response.json()
            startups = data.get("data", {}).get("startupSearchResults", {}).get("startups", [])
            for startup in startups:
                for job in startup.get("jobs", []):
                    jobs.append({
                        "title":       job.get("title", ""),
                        "company":     startup.get("name", ""),
                        "location":    ", ".join(job.get("locationNames", [])),
                        "description": job.get("description", ""),
                        "url":         job.get("applyUrl", ""),
                        "salary":      "Not specified",
                        "job_type":    job.get("jobType", ""),
                        "posted_at":   "",
                        "source":      "WellFound",
                        "remote":      "remote" in ", ".join(job.get("locationNames", [])).lower()
                    })
        print(f"WellFound: fetched {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"WellFound error: {e}")
        return []