import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.jsearch import fetch_jsearch_jobs
from fetchers.remotive import fetch_remotive_jobs
from fetchers.arbeitnow import fetch_arbeitnow_jobs
from fetchers.themuse import fetch_themuse_jobs
from fetchers.greenhouse import fetch_greenhouse_jobs
from fetchers.wellfound import fetch_wellfound_jobs
from fetchers.otta import fetch_otta_jobs
from fetchers.workable import fetch_workable_jobs

# All available sources
SOURCES = {
    "1": {
        "name":           "JSearch (LinkedIn + Indeed + Glassdoor)",
        "key":            "jsearch",
        "fetch":          fetch_jsearch_jobs,
        "needs_location": True,
        "supports_date":  True
    },
    "2": {
        "name":           "Remotive (Remote Tech Jobs)",
        "key":            "remotive",
        "fetch":          fetch_remotive_jobs,
        "needs_location": False,
        "supports_date":  False
    },
    "3": {
        "name":           "Arbeitnow (Global Tech Jobs)",
        "key":            "arbeitnow",
        "fetch":          fetch_arbeitnow_jobs,
        "needs_location": False,
        "supports_date":  False
    },
    "4": {
        "name":           "The Muse (US Jobs)",
        "key":            "themuse",
        "fetch":          fetch_themuse_jobs,
        "needs_location": False,
        "supports_date":  False
    },
    "5": {
        "name":           "Greenhouse (Tech Startups)",
        "key":            "greenhouse",
        "fetch":          fetch_greenhouse_jobs,
        "needs_location": False,
        "supports_date":  False
    },
    "6": {
        "name":           "WellFound (Startup + Equity Jobs)",
        "key":            "wellfound",
        "fetch":          fetch_wellfound_jobs,
        "needs_location": False,
        "supports_date":  False
    },
    "7": {
        "name":           "Otta (Tech Growth Companies)",
        "key":            "otta",
        "fetch":          fetch_otta_jobs,
        "needs_location": False,
        "supports_date":  False
    },
    "8": {
        "name":           "RemoteOK (Remote Jobs)",
        "key":            "remoteok",
        "fetch":          fetch_workable_jobs,
        "needs_location": False,
        "supports_date":  False
    },
}

# Date filter options
DATE_FILTERS = {
    "1": {"label": "Last 24 hours", "jsearch": "today",  "hours": 24},
    "2": {"label": "Last 2 days",   "jsearch": "3days",  "hours": 48},
    "3": {"label": "Last 3 days",   "jsearch": "3days",  "hours": 72},
    "4": {"label": "Last 7 days",   "jsearch": "week",   "hours": 168},
    "5": {"label": "Last 30 days",  "jsearch": "month",  "hours": 720},
}


def filter_by_date(jobs: list, hours: int) -> list:
    """Filter jobs posted within the last N hours."""
    if hours == 720:
        return jobs
    cutoff   = datetime.utcnow() - timedelta(hours=hours)
    filtered = []
    for job in jobs:
        posted = job.get("posted_at", "")
        if not posted:
            filtered.append(job)
            continue
        try:
            if isinstance(posted, str) and posted:
                posted_clean = posted.replace("Z", "+00:00")
                posted_dt    = datetime.fromisoformat(posted_clean).replace(tzinfo=None)
                if posted_dt >= cutoff:
                    filtered.append(job)
            else:
                filtered.append(job)
        except Exception:
            filtered.append(job)
    return filtered


def fetch_all_jobs(
    job_title:        str,
    location:         str  = "USA",
    limit:            int  = 20,
    selected_sources: list = None,
    date_filter_key:  str  = "1"
) -> list:
    """
    Fetches jobs from selected sources filtered by job title and date.
    Returns exactly 'limit' jobs deduplicated by URL.
    """
    if selected_sources is None:
        selected_sources = list(SOURCES.keys())

    date_config  = DATE_FILTERS.get(date_filter_key, DATE_FILTERS["1"])
    jsearch_date = date_config["jsearch"]
    hours        = date_config["hours"]

    print(f"\nSearching for : '{job_title}'")
    print(f"Location      : {location}")
    print(f"Date filter   : {date_config['label']}")
    print(f"Sources       : {len(selected_sources)} selected")
    print(f"Jobs wanted   : {limit}")
    print("-" * 50)

    all_jobs = []

    for key in selected_sources:
        source = SOURCES.get(key)
        if not source:
            continue
        try:
            if source["needs_location"] and source["supports_date"]:
                jobs = source["fetch"](job_title, location, jsearch_date)
            elif source["needs_location"]:
                jobs = source["fetch"](job_title, location)
            else:
                jobs = source["fetch"](job_title)

            # Apply date filter for sources that don't support it natively
            if not source["supports_date"]:
                jobs = filter_by_date(jobs, hours)

            all_jobs += jobs

        except Exception as e:
            print(f"Error from {source['name']}: {e}")
            continue

    # Deduplicate by URL
    seen_urls   = set()
    unique_jobs = []
    for job in all_jobs:
        url = job.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_jobs.append(job)

    # Sort by source
    unique_jobs.sort(key=lambda x: x.get("source", ""))

    # Apply limit
    limited_jobs = unique_jobs[:limit]

    print(f"\n{'=' * 50}")
    print(f"TOTAL UNIQUE JOBS FOUND : {len(unique_jobs)}")
    print(f"SHOWING                 : {len(limited_jobs)}")
    print(f"{'=' * 50}\n")

    return limited_jobs


if __name__ == "__main__":
    # Step 1 — Job title
    job_title = input("Enter job title to search: ").strip()

    # Step 2 — Location
    location = input("Enter location (press Enter for USA): ").strip() or "USA"

    # Step 3 — Date filter
    print("\nHow recently posted?")
    print("─" * 40)
    for key, val in DATE_FILTERS.items():
        print(f"  [{key}] {val['label']}")
    print("─" * 40)
    date_choice = input("Your choice (press Enter for last 24 hours): ").strip() or "1"
    if date_choice not in DATE_FILTERS:
        date_choice = "1"
    print(f"Selected: {DATE_FILTERS[date_choice]['label']}")

    # Step 4 — Portal selection
    print("\nSelect job portals:")
    print("─" * 55)
    for key, source in SOURCES.items():
        print(f"  [{key}] {source['name']}")
    print("─" * 55)
    print("  [A] All portals")
    print()
    choice = input("Your choice (e.g. 1,2,3 or A for all): ").strip().upper()

    if choice == "A" or choice == "":
        selected = list(SOURCES.keys())
    else:
        selected = [c.strip() for c in choice.split(",") if c.strip() in SOURCES]
        if not selected:
            print("Invalid — using all sources")
            selected = list(SOURCES.keys())

    print(f"\nSelected portals:")
    for key in selected:
        print(f"  ✓ {SOURCES[key]['name']}")

    # Step 5 — How many jobs
    limit_str = input("\nHow many jobs to show? (press Enter for 20): ").strip()
    limit     = int(limit_str) if limit_str.isdigit() else 20

    # Step 6 — Fetch and display
    jobs = fetch_all_jobs(job_title, location, limit, selected, date_choice)

    if not jobs:
        print("No jobs found. Try different filters.")
    else:
        print(f"Showing {len(jobs)} jobs:\n")
        print("=" * 60)
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job['title']}")
            print(f"   Company  : {job['company']}")
            print(f"   Location : {job['location']}")
            print(f"   Posted   : {job['posted_at'][:10] if job['posted_at'] else 'Unknown'}")
            print(f"   Source   : {job['source']}")
            print(f"   Remote   : {'Yes' if job['remote'] else 'No'}")
            print(f"   Salary   : {job['salary']}")
            print(f"   URL      : {job['url']}")
            print()