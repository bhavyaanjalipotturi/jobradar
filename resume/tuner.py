import os
from anthropic import Anthropic
from dotenv import load_dotenv
from resume.ats_scorer import calculate_ats_score, format_score_report

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def tune_resume(resume_text: str, job_description: str, job_title: str = "") -> dict:
    """
    Uses Claude AI to rewrite the resume to match the job description.
    Returns tuned resume text and before/after ATS scores.
    """

    # Score BEFORE tuning
    score_before = calculate_ats_score(resume_text, job_description)

    # Build the AI prompt
    prompt = f"""You are an expert resume writer and ATS optimization specialist.

I need you to transform the resume below to land an interview for the job description provided.
Follow ALL these instructions carefully:

GOAL: Rewrite the resume so it scores 95%+ ATS match with the job description, sounds
human-written (not AI), and compels the hiring manager to call for an interview.

INSTRUCTIONS:

1. ATS Optimization
   - Extract all keywords, skills, tools, and phrases from the job description
   - Naturally embed them throughout the resume (summary, skills, bullet points)
   - Use the EXACT terminology the job description uses — not synonyms

2. Skills Gap — Fill Realistically, Never Fabricate
   - Identify any required skills or experience missing from the resume
   - Do NOT invent experience that does not exist
   - Instead, look at the existing background and reframe it to show how it connects
     to the missing requirement
   - If something similar or related exists, position it as transferable experience
   - If a skill is completely absent with no related background, add it to the Skills
     section only at a beginner/familiar level — and FLAG it clearly
   - The goal is to present real experience in the most relevant and strategic way

3. Rewrite Bullet Points — Human, Punchy, Results-Driven
   - Start every bullet with a strong action verb
   - Follow the format: Action + Task + Result/Impact (quantify wherever possible)
   - Make it sound like a real experienced human wrote it
   - AVOID these overused AI phrases: "spearheaded", "leveraged", "utilized",
     "passionate", "dynamic", "synergy", "robust"

4. Metrics-Driven Achievements — ABSOLUTE MANDATORY REQUIREMENT
   - You MUST include EXACTLY 3 to 5 bullet points with REAL NUMBERS in them
   - These are NON-NEGOTIABLE — if you skip this the resume is incomplete
   - Place them inside the experience and projects sections as bullet points
   - Every metrics bullet MUST contain at least one specific number like:
     * Percentages: 60%, 87%, 99%, 40%
     * Counts: 12+ pipelines, 5 models, 8 workflows, 50K+ records
     * Time: reduced by 3 hours, delivered in 2 weeks
     * People: served 25+ stakeholders, supported 10+ clients
   - Use these EXACT example formats — fill in the blanks with realistic numbers:
     * "Built and maintained [X]+ Python-based pipelines processing [X]K+ daily records"
     * "Automated [X]+ recurring workflows reducing manual effort by [X]%"
     * "Trained and deployed [X] ML models achieving [X]% accuracy and [X] F1-score"
     * "Developed data pipelines processing [X]K+ records with [X]% data quality rate"
     * "Reduced data processing time by [X]% through automated Python scripting"
   - Estimate numbers conservatively if not explicitly stated:
     * Accenture (large enterprise) = millions of records, dozens of pipelines
     * Capstone project (academic) = thousands of records, 3-5 models
     * Internship (small company) = hundreds of records, 2-3 pipelines
   - DO NOT write vague bullets like "improved efficiency" — ALWAYS add a number
   - After writing the resume, count your metrics bullets — if less than 3, add more

5. Professional Summary
   - Write a 3-4 line summary tailored specifically to this job
   - Make it sound confident, natural, and specific — not a generic template
   - Include the job title from the posting and top 2-3 matching strengths
   - Reflect only what is genuinely present in the background

6. Interview-Magnet Formatting
   - Keep formatting clean and ATS-parseable (no tables, columns, or graphics)
   - Prioritize the most relevant experience at the top
   - Remove or trim anything irrelevant to this specific role

7. Final Report — Give a Summary at the END:
   - Estimated ATS match score (target: 95%+)
   - List of keywords successfully added
   - List of gaps that were realistically bridged and how
   - List of all [METRICS] bullets added with explanation of how numbers were estimated
   - List of any FLAGGED skills the candidate needs to personally verify
   - 2-3 tips to further strengthen the application

---

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description}

---

ORIGINAL RESUME:
{resume_text}

---

Now write the COMPLETE rewritten resume first, then the Final Report.
Separate the resume from the report with this exact line:
===REPORT===

IMPORTANT:
- Write the FULL resume — do not skip any section
- Make sure 3-5 [METRICS] bullets are clearly visible in the resume
- The resume must be ready to copy and paste directly into a Word document
"""

    print("\nAI is analyzing and rewriting your resume...")
    print("This takes 30-60 seconds...\n")

    try:
        message = client.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 4000,
            messages   = [{"role": "user", "content": prompt}]
        )

        full_response = message.content[0].text

        # Split resume from report
        if "===REPORT===" in full_response:
            parts        = full_response.split("===REPORT===")
            tuned_resume = parts[0].strip()
            final_report = parts[1].strip() if len(parts) > 1 else ""
        else:
            tuned_resume = full_response
            final_report = ""

        # Score AFTER tuning
        score_after = calculate_ats_score(tuned_resume, job_description)

        return {
            "tuned_resume":  tuned_resume,
            "final_report":  final_report,
            "score_before":  score_before,
            "score_after":   score_after,
            "before_report": format_score_report(score_before, "ATS Score BEFORE"),
            "after_report":  format_score_report(score_after,  "ATS Score AFTER"),
        }

    except Exception as e:
        return {"error": str(e)}


def save_tuned_resume(tuned_text: str, output_path: str = "tuned_resume.txt") -> str:
    """Save tuned resume as text file."""
    with open(output_path, "w") as f:
        f.write(tuned_text)
    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("       AI RESUME TUNER — JobRadar")
    print("=" * 60)

    # Step 1 — Resume path
    resume_path = input("\nEnter path to your resume PDF: ").strip()

    # Step 2 — Job description
    print("\nPaste the job description below.")
    print("Press Enter twice when done:\n")
    lines = []
    empty_count = 0
    while True:
        line = input()
        if line == "":
            empty_count += 1
            if empty_count >= 2:
                break
        else:
            empty_count = 0
        lines.append(line)
    job_description = "\n".join(lines).strip()

    # Step 3 — Job title
    job_title = input("\nEnter the job title: ").strip()

    # Step 4 — Parse resume
    from resume.parser import parse_resume_pdf
    print("\nReading your resume...")
    try:
        resume_data = parse_resume_pdf(resume_path)
        resume_text = resume_data["full_text"]
        print(f"Resume parsed — {len(resume_text)} characters read")
        print(f"Name detected : {resume_data['name']}")
    except Exception as e:
        print(f"Error reading resume: {e}")
        exit(1)

    # Step 5 — Show score BEFORE
    print("\n" + "=" * 60)
    score_before = calculate_ats_score(resume_text, job_description)
    print(format_score_report(score_before, "ATS Score BEFORE Tuning"))

    # Step 6 — Tune the resume
    result = tune_resume(resume_text, job_description, job_title)

    if "error" in result:
        print(f"\nError: {result['error']}")
        exit(1)

    # Step 7 — Show score AFTER
    print(result["after_report"])

    # Step 8 — Show full updated resume
    print("\n" + "=" * 60)
    print("   UPDATED RESUME — COPY THIS INTO YOUR WORD DOCUMENT")
    print("=" * 60 + "\n")
    print(result["tuned_resume"])
    print("\n" + "=" * 60)

    # Step 9 — Save to file
    output_path = save_tuned_resume(result["tuned_resume"])
    print(f"\nResume also saved to: {output_path}")
    print("Open it in VS Code: code tuned_resume.txt")

    # Step 10 — Show final report
    print("\n" + "=" * 60)
    print("   FINAL REPORT")
    print("=" * 60 + "\n")
    print(result["final_report"])

    print("\n" + "=" * 60)
    print("Done! Your resume is ready.")
    print("=" * 60)