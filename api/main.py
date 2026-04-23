import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import shutil

from fetchers.all_jobs import fetch_all_jobs, SOURCES, DATE_FILTERS
from resume.parser import parse_resume_pdf
from resume.ats_scorer import calculate_ats_score, format_score_report
from resume.tuner import tune_resume, save_tuned_resume
from fastapi.responses import FileResponse

# Create the FastAPI app
app = FastAPI(
    title="JobRadar API",
    description="AI-powered job aggregator and resume tuner",
    version="1.0.0"
)

# Allow Streamlit frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response Models ───────────────────────────────────────────────────

class JobSearchRequest(BaseModel):
    job_title:        str
    location:         Optional[str] = "USA"
    limit:            Optional[int] = 20
    selected_sources: Optional[List[str]] = None
    date_filter_key:  Optional[str] = "1"

class JobSearchResponse(BaseModel):
    total:        int
    jobs:         list
    sources_used: list

class ATSScoreRequest(BaseModel):
    resume_text:     str
    job_description: str

class ATSScoreResponse(BaseModel):
    total_score:      int
    keyword_score:    int
    skills_score:     int
    exp_score:        int
    edu_score:        int
    title_score:      int
    format_score:     int
    matched_keywords: list
    missing_keywords: list
    missing_skills:   list
    report:           str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":  "JobRadar API is running",
        "version": "1.0.0",
        "endpoints": [
            "POST /jobs/search",
            "POST /resume/score",
            "POST /resume/tune",
            "GET  /jobs/sources",
            "GET  /jobs/date-filters",
            "GET  /health"
        ]
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "JobRadar"}


@app.get("/jobs/sources")
def get_sources():
    """Returns all available job portals."""
    return {
        "sources": [
            {"key": key, "name": source["name"]}
            for key, source in SOURCES.items()
        ]
    }


@app.get("/jobs/date-filters")
def get_date_filters():
    """Returns all available date filters."""
    return {
        "filters": [
            {"key": key, "label": val["label"]}
            for key, val in DATE_FILTERS.items()
        ]
    }


@app.post("/jobs/search", response_model=JobSearchResponse)
def search_jobs(request: JobSearchRequest):
    """
    Search jobs from selected portals.
    Returns deduplicated list of jobs.
    """
    jobs = fetch_all_jobs(
        job_title        = request.job_title,
        location         = request.location or "USA",
        limit            = request.limit or 20,
        selected_sources = request.selected_sources,
        date_filter_key  = request.date_filter_key or "1"
    )

    sources_used = list(set(job.get("source", "") for job in jobs))

    return JobSearchResponse(
        total        = len(jobs),
        jobs         = jobs,
        sources_used = sources_used
    )


@app.post("/resume/score", response_model=ATSScoreResponse)
def score_resume(request: ATSScoreRequest):
    """
    Calculate ATS score for a resume vs job description.
    """
    score  = calculate_ats_score(request.resume_text, request.job_description)
    report = format_score_report(score, "ATS Score")

    return ATSScoreResponse(
        total_score      = score["total_score"],
        keyword_score    = score["keyword_score"],
        skills_score     = score["skills_score"],
        exp_score        = score["exp_score"],
        edu_score        = score["edu_score"],
        title_score      = score["title_score"],
        format_score     = score["format_score"],
        matched_keywords = score["matched_keywords"],
        missing_keywords = score["missing_keywords"],
        missing_skills   = score["missing_skills"],
        report           = report
    )


@app.post("/resume/tune")
async def tune_resume_endpoint(
    file:            UploadFile = File(...),
    job_description: str        = Form(...),
    job_title:       str        = Form(...)
):
    """
    Upload a PDF resume and get an AI-tuned version back.
    Returns tuned resume as downloadable PDF.
    """
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Parse the resume
        resume_data = parse_resume_pdf(tmp_path)
        resume_text = resume_data["full_text"]

        # Tune the resume
        result = tune_resume(resume_text, job_description, job_title)

        if "error" in result:
            return {"error": result["error"]}

        # Save tuned resume as PDF
        output_path = save_tuned_resume(
            result["tuned_resume"],
            output_path="tuned_resume.pdf"
        )

        return {
            "score_before":  result["score_before"]["total_score"],
            "score_after":   result["score_after"]["total_score"],
            "before_report": result["before_report"],
            "after_report":  result["after_report"],
            "tuned_resume":  result["tuned_resume"],
            "final_report":  result["final_report"],
            "pdf_ready":     True
        }

    finally:
        # Clean up temp file
        os.unlink(tmp_path)


@app.get("/resume/download")
def download_resume():
    """Download the last tuned resume as PDF."""
    if os.path.exists("tuned_resume.pdf"):
        return FileResponse(
            path         = "tuned_resume.pdf",
            filename     = "tuned_resume.pdf",
            media_type   = "application/pdf"
        )
    return {"error": "No tuned resume found. Please tune your resume first."}