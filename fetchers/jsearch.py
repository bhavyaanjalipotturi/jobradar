import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

def fetch_jsearch_jobs(query: str, location: str = "USA", date_filter: str = "today") -> list:
    """
    Fetches jobs from LinkedIn, Indeed, Glassdoor via JSearch API.
    date_filter options: today, 3days, week, month
    """
    if not RAPIDAPI_KEY:
        print("Warning: RAPIDAPI_KEY not found in .env")
        return []

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key":  RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {
        "query":            f'"{query}" in {location}',
        "page":             "1",
        "num_pages":        "3",
        "date_posted":      date_filter,
        "remote_jobs_only": "false"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        jobs = []
        for job in data.get("data", []):
            city        = job.get("job_city") or ""
            country     = job.get("job_country") or ""
            location_str = f"{city}, {country}".strip(", ")

            jobs.append({
                "title":       job.get("job_title") or "",
                "company":     job.get("employer_name") or "",
                "location":    location_str,
                "description": job.get("job_description") or "",
                "url":         job.get("job_apply_link") or "",
                "salary":      job.get("job_salary") or "Not specified",
                "job_type":    job.get("job_employment_type") or "",
                "posted_at":   job.get("job_posted_at_datetime_utc") or "",
                "source":      "JSearch (LinkedIn/Indeed/Glassdoor)",
                "remote":      job.get("job_is_remote") or False
            })
        print(f"JSearch: fetched {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"JSearch error: {e}")
        return []