import requests

def fetch_otta_jobs(query: str) -> list:
    """
    Fetches tech jobs from Otta.
    No API key needed.
    """
    url = "https://api.otta.com/graphql"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": """
        query JobSearch($query: String!) {
          jobs(query: $query) {
            title
            company { name }
            locationString
            externalUrl
            employmentType
            salaryRange { min max currency }
          }
        }
        """,
        "variables": {"query": query}
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        jobs = []
        if response.status_code == 200:
            data = response.json()
            for job in data.get("data", {}).get("jobs", []):
                salary = "Not specified"
                sal    = job.get("salaryRange", {})
                if sal:
                    salary = f"{sal.get('min','')}-{sal.get('max','')} {sal.get('currency','')}"
                jobs.append({
                    "title":       job.get("title", ""),
                    "company":     job.get("company", {}).get("name", ""),
                    "location":    job.get("locationString", ""),
                    "description": "",
                    "url":         job.get("externalUrl", ""),
                    "salary":      salary,
                    "job_type":    job.get("employmentType", ""),
                    "posted_at":   "",
                    "source":      "Otta",
                    "remote":      "remote" in job.get("locationString", "").lower()
                })
        print(f"Otta: fetched {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"Otta error: {e}")
        return []