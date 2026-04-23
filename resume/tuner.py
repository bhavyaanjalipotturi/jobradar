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
   - List of all metrics bullets added with explanation of how numbers were estimated
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
- Make sure 3-5 metrics bullets with real numbers are clearly visible
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

        # Remove [METRICS] tags from resume — keep content, remove label
        tuned_resume = tuned_resume.replace("[METRICS] ", "")
        tuned_resume = tuned_resume.replace("[METRICS]", "")

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


def save_tuned_resume(tuned_text: str, output_path: str = "tuned_resume.pdf") -> str:
    """Save tuned resume as PDF file."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    for line in tuned_text.split("\n"):
        line = line.strip()

        if not line:
            pdf.ln(3)
            continue

        # Remove markdown symbols
        line = line.replace("**", "").replace("##", "").replace("#", "")
        line = line.replace("---", "").replace("*", "")
        line = line.strip()

        if not line:
            pdf.ln(3)
            continue

        # Detect section headers
        is_header = (
            line.isupper() or
            (line.endswith(":") and len(line) < 50) or
            line.startswith("PROFESSIONAL") or
            line.startswith("TECHNICAL") or
            line.startswith("EXPERIENCE") or
            line.startswith("EDUCATION") or
            line.startswith("PROJECTS") or
            line.startswith("SKILLS") or
            line.startswith("CERTIFICATIONS") or
            line.startswith("SUMMARY")
        )

        is_name = pdf.page_no() == 1 and pdf.get_y() < 30

        try:
            if is_name and len(line) < 50 and not line.startswith("-"):
                pdf.set_font("Helvetica", "B", 16)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 8, line, ln=True, align="C")
                pdf.ln(2)

            elif is_header:
                pdf.ln(3)
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 0, 128)
                pdf.cell(0, 7, line.upper(), ln=True)
                pdf.set_draw_color(0, 0, 128)
                pdf.set_line_width(0.3)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(2)
                pdf.set_text_color(0, 0, 0)

            elif line.startswith("-") or line.startswith("•"):
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(0, 0, 0)
                bullet_text = line.lstrip("-•").strip()
                pdf.set_x(15)
                pdf.cell(5, 5, "•", ln=False)
                pdf.set_x(20)
                pdf.multi_cell(175, 5, bullet_text)

            elif "|" in line and len(line) < 100:
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(0, 5, line, ln=True, align="C")

            elif line.startswith("Tech Stack"):
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 5, line)

            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 5, line)

        except Exception:
            continue

    pdf.output(output_path)
    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("       AI RESUME TUNER — JobRadar")
    print("=" * 60)

    # Step 1 — File upload
    print("\nTo upload your resume:")
    print("Option 1: Drag and drop your PDF into this terminal window")
    print("Option 2: Type the full path to your PDF file")
    print()
    resume_path = input("Upload your resume (drag PDF here or type path): ").strip()

    # Remove quotes added by Mac when dragging files
    resume_path = resume_path.strip("'").strip('"')

    # Check file exists
    if not os.path.exists(resume_path):
        print(f"\nFile not found: {resume_path}")
        print("Please check the path and try again.")
        exit(1)

    print(f"\nResume uploaded: {os.path.basename(resume_path)}")

    # Step 2 — Job description
    print("\nPaste the job description below.")
    print("Press Enter twice when done:\n")
    lines       = []
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
        print(f"Resume uploaded successfully — {len(resume_text)} characters read")
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

    # Step 9 — Save as PDF
    output_path = save_tuned_resume(result["tuned_resume"])
    print(f"\nResume saved as PDF: {output_path}")
    print(f"Open it with: open {output_path}")

    # Step 10 — Show final report
    print("\n" + "=" * 60)
    print("   FINAL REPORT")
    print("=" * 60 + "\n")
    print(result["final_report"])

    print("\n" + "=" * 60)
    print("Done! Your tuned resume is ready.")
    print("=" * 60)