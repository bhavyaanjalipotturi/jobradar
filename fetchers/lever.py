import requests

LEVER_COMPANIES = [
    "netflix", "reddit", "coinbase", "brex",
    "rippling", "loom", "linear", "mercury",
    "deel", "remote", "lattice", "dbt-labs"
]

def fetch_lever_jobs(query: str) -> list:
    jobs = []
    query_words = query.lower().split()
    for company in LEVER_COMPANIES:
        try:
            url      = f"https://api.lever.co/v0/postings/{company}"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            for job in data:
                title = job.get("text", "").lower()
                if any(word in title for word in query_words):
                    location = job.get("categories", {}).get("location", "")
                    jobs.append({
                        "title":       job.get("text", ""),
                        "company":     company.title(),
                        "location":    location,
                        "description": job.get("descriptionPlain", ""),
                        "url":         job.get("hostedUrl", ""),
                        "salary":      "Not specified",
                        "job_type":    job.get("categories", {}).get("commitment", ""),
                        "posted_at":   "",
                        "source":      "Lever",
                        "remote":      "remote" in location.lower()
                    })
        except Exception:
            continue
    print(f"Lever: fetched {len(jobs)} jobs")
    return jobs