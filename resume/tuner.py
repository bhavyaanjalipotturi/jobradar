import os
from anthropic import Anthropic
from dotenv import load_dotenv
from resume.ats_scorer import calculate_ats_score, format_score_report, calculate_human_score

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def tune_resume(resume_text: str, job_description: str, job_title: str = "") -> dict:
    """
    Uses Claude AI to rewrite the resume to match the job description.
    Returns tuned resume text and before/after ATS scores.
    """
    score_before = calculate_ats_score(resume_text, job_description)

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
   - If a skill is completely absent, add it to Skills section at beginner level and FLAG it

3. Human-Written Tone — ABSOLUTELY MANDATORY
   - The entire resume MUST read like a real human wrote it
   - NEVER use: spearheaded, leveraged, utilized, passionate, dynamic, synergy,
     robust, innovative, cutting-edge, orchestrated, championed, catalyzed,
     streamlined, transformative, holistic, proactively
   - USE instead: built, wrote, ran, fixed, helped, worked, set up, cut, led,
     grew, saved, shipped, trained, found, made, got

4. Metrics-Driven Achievements — MANDATORY
   - You MUST include EXACTLY 3 to 5 bullet points with REAL NUMBERS
   - Every metrics bullet MUST contain at least one specific number
   - Examples:
     * "Built 12+ Python pipelines processing 500K+ daily records"
     * "Automated 8+ workflows reducing manual effort by 60%"
     * "Trained 5 ML models achieving 87% accuracy and 0.82 F1-score"

5. Professional Summary
   - Write a 3-4 line summary tailored specifically to this job
   - Include the exact job title and top 2-3 matching strengths
   - Sound confident and specific — not generic

6. Interview-Magnet Formatting
   - Keep formatting ATS-parseable (no tables, columns, graphics)
   - Prioritize most relevant experience at the top

7. Final Report at the END:
   - Estimated ATS match score (target 95%+)
   - Keywords successfully added
   - Gaps bridged and how
   - Metrics bullets added with number explanations
   - Flagged skills to verify
   - 2-3 tips to strengthen application

---
JOB TITLE: {job_title}
JOB DESCRIPTION:
{job_description}
---
ORIGINAL RESUME:
{resume_text}
---

Write the COMPLETE rewritten resume first, then the Final Report.
Separate with: ===REPORT===

IMPORTANT: Write the FULL resume. Include 3-5 metrics bullets with real numbers.
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

        if "===REPORT===" in full_response:
            parts        = full_response.split("===REPORT===")
            tuned_resume = parts[0].strip()
            final_report = parts[1].strip() if len(parts) > 1 else ""
        else:
            tuned_resume = full_response
            final_report = ""

        tuned_resume = tuned_resume.replace("[METRICS] ", "")
        tuned_resume = tuned_resume.replace("[METRICS]", "")

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


def retune_resume(
    tuned_resume_text: str,
    job_description:   str,
    job_title:         str,
    previous_score:    dict
) -> dict:
    """
    Re-tunes an already tuned resume using the ATS report findings.
    Specifically targets missing keywords, skills and gaps to push score above 95.
    """
    score_before     = calculate_ats_score(tuned_resume_text, job_description)
    missing_keywords = score_before.get("missing_keywords", [])
    missing_skills   = score_before.get("missing_skills", [])
    keyword_score    = score_before.get("keyword_score", 0)
    skills_score     = score_before.get("skills_score", 0)
    edu_score        = score_before.get("edu_score", 0)
    title_score      = score_before.get("title_score", 0)
    format_score     = score_before.get("format_score", 0)
    total_score      = score_before.get("total_score", 0)

    prompt = f"""You are an expert ATS resume optimization specialist.

The resume below scored {total_score}/100. Push it above 95/100 by fixing EXACTLY what is missing.

CURRENT SCORE:
- Keyword Match   : {keyword_score}/30
- Skills Match    : {skills_score}/25
- Experience      : {score_before.get('exp_score', 0)}/20
- Education       : {edu_score}/10
- Job Title Match : {title_score}/10
- Format          : {format_score}/5

MISSING KEYWORDS TO ADD:
{', '.join(missing_keywords) if missing_keywords else 'None'}

MISSING SKILLS TO ADD:
{', '.join(missing_skills) if missing_skills else 'None'}

INSTRUCTIONS:
1. Add every missing keyword naturally into summary, skills, bullets
2. Add every missing skill to the Skills section
3. The exact job title "{job_title}" MUST appear in the Professional Summary
4. Keep all existing metrics bullets — add 1-2 more if possible
5. DO NOT remove anything good that is already in the resume

RESUME:
{tuned_resume_text}

JOB DESCRIPTION:
{job_description}

Write COMPLETE improved resume then add:
===REPORT===
- Estimated ATS score
- Missing keywords added and where
- Missing skills added
- Confirmation job title appears in summary
- 2 final tips
"""

    print("\nRe-tuning resume targeting missing requirements...")

    try:
        message = client.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 4000,
            messages   = [{"role": "user", "content": prompt}]
        )

        full_response = message.content[0].text

        if "===REPORT===" in full_response:
            parts        = full_response.split("===REPORT===")
            tuned_resume = parts[0].strip()
            final_report = parts[1].strip() if len(parts) > 1 else ""
        else:
            tuned_resume = full_response
            final_report = ""

        tuned_resume = tuned_resume.replace("[METRICS] ", "")
        tuned_resume = tuned_resume.replace("[METRICS]", "")

        score_after = calculate_ats_score(tuned_resume, job_description)

        return {
            "tuned_resume":  tuned_resume,
            "final_report":  final_report,
            "score_before":  score_before,
            "score_after":   score_after,
            "before_report": format_score_report(score_before, "Score Before Re-tune"),
            "after_report":  format_score_report(score_after,  "Score After Re-tune"),
        }

    except Exception as e:
        return {"error": str(e)}


def rehumanize_resume(resume_text: str, job_description: str, job_title: str) -> dict:
    """
    Takes an already tuned resume and rewrites it to sound more human.
    Keeps all content and meaning — only changes the tone and language.
    """
    score_before = calculate_human_score(resume_text)

    prompt = f"""You are an expert resume editor who specializes in making resumes
sound like they were written by a real human being — not AI.

Rewrite the resume below so it sounds 100% human-written while keeping
EVERY piece of information, achievement, and meaning intact.

CRITICAL RULES:

1. NEVER CHANGE THE MEANING
   - Keep every job title, company, date, and achievement exactly as is
   - Keep all numbers and metrics exactly as is
   - Keep all technical skills and keywords exactly as is
   - Only change HOW things are said — not WHAT is said

2. MAKE IT SOUND HUMAN
   - Write like a smart professional talking naturally
   - Use short punchy sentences mixed with medium ones
   - Start bullets with simple strong verbs: built, wrote, ran, led, cut,
     fixed, helped, set up, grew, saved, shipped, trained, found
   - NEVER use: spearheaded, leveraged, utilized, orchestrated, championed,
     catalyzed, streamlined, paradigm, synergy, robust, innovative,
     cutting-edge, transformative, holistic, proactively, dynamic
   - Vary sentence structure — not every bullet the same pattern
   - Occasionally use contractions: didn't, we'd, wasn't, it's

3. HUMAN WRITING EXAMPLES
   - "Built a pipeline that cut processing time by 40%" ✅
   - "Developed an optimized pipeline solution that facilitated a 40%
      reduction in processing time" ❌
   - "Worked with the team to ship a new dashboard" ✅
   - "Collaborated with cross-functional stakeholders to deliver
      a comprehensive dashboard solution" ❌

4. PROFESSIONAL SUMMARY
   - Write like a confident person introducing themselves naturally
   - Max 4 lines — direct and specific
   - Sound excited but not robotic

5. KEEP ATS KEYWORDS
   - All job description keywords must still appear naturally
   - Technical terms like Python, FastAPI, LangChain are fine as-is

RESUME TO REHUMANIZE:
{resume_text}

JOB TITLE: {job_title}
JOB DESCRIPTION CONTEXT: {job_description[:500]}

Write the COMPLETE rehumanized resume.
Then add:
===HUMAN_REPORT===
- Human-written score estimate (target 95%+)
- AI phrases removed and what replaced them
- 2 before vs after examples
"""

    print("\nRewriting resume in human tone...")

    try:
        message = client.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 4000,
            messages   = [{"role": "user", "content": prompt}]
        )

        full_response = message.content[0].text

        if "===HUMAN_REPORT===" in full_response:
            parts        = full_response.split("===HUMAN_REPORT===")
            human_resume = parts[0].strip()
            human_report = parts[1].strip() if len(parts) > 1 else ""
        else:
            human_resume = full_response
            human_report = ""

        score_after = calculate_human_score(human_resume)

        return {
            "human_resume":  human_resume,
            "human_report":  human_report,
            "score_before":  score_before,
            "score_after":   score_after,
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

        line = line.replace("**", "").replace("##", "").replace("#", "")
        line = line.replace("---", "").replace("*", "")
        line = line.strip()

        if not line:
            pdf.ln(3)
            continue

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

    print("\nTo upload your resume:")
    print("Option 1: Drag and drop your PDF into this terminal window")
    print("Option 2: Type the full path to your PDF file")
    print()
    resume_path = input("Upload your resume (drag PDF here or type path): ").strip()
    resume_path = resume_path.strip("'").strip('"')

    if not os.path.exists(resume_path):
        print(f"\nFile not found: {resume_path}")
        exit(1)

    print(f"\nResume uploaded: {os.path.basename(resume_path)}")

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

    job_title = input("\nEnter the job title: ").strip()

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

    print("\n" + "=" * 60)
    score_before = calculate_ats_score(resume_text, job_description)
    print(format_score_report(score_before, "ATS Score BEFORE Tuning"))

    result = tune_resume(resume_text, job_description, job_title)

    if "error" in result:
        print(f"\nError: {result['error']}")
        exit(1)

    print(result["after_report"])

    print("\n" + "=" * 60)
    print("   UPDATED RESUME")
    print("=" * 60 + "\n")
    print(result["tuned_resume"])

    output_path = save_tuned_resume(result["tuned_resume"])
    print(f"\nResume saved as PDF: {output_path}")
    print(f"Open it with: open {output_path}")

    print("\n" + "=" * 60)
    print("   FINAL REPORT")
    print("=" * 60 + "\n")
    print(result["final_report"])
    print("\n" + "=" * 60)
    print("Done! Your tuned resume is ready.")
    print("=" * 60)