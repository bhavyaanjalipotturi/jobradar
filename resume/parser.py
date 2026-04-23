import os
import pdfplumber

def parse_resume_pdf(file_path: str) -> dict:
    """
    Reads a PDF resume and extracts all text content.
    Returns structured dictionary with resume sections.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    full_text = ""

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
    except Exception as e:
        raise Exception(f"Error reading PDF: {e}")

    if not full_text.strip():
        raise Exception("Could not extract text from PDF. Make sure it is not a scanned image.")

    # Split into lines for section detection
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]

    # Detect sections
    sections = {
        "full_text":    full_text,
        "name":         extract_name(lines),
        "contact":      extract_contact(full_text),
        "summary":      extract_section(full_text, ["summary", "objective", "profile", "about"]),
        "experience":   extract_section(full_text, ["experience", "work history", "employment"]),
        "education":    extract_section(full_text, ["education", "academic", "degree"]),
        "skills":       extract_section(full_text, ["skills", "technical skills", "competencies", "technologies"]),
        "projects":     extract_section(full_text, ["projects", "portfolio", "work samples"]),
        "certifications": extract_section(full_text, ["certifications", "certificates", "licenses"]),
    }

    return sections


def extract_name(lines: list) -> str:
    """First non-empty line is usually the name."""
    for line in lines[:5]:
        if len(line) > 2 and len(line) < 50:
            if not any(char in line for char in ["@", "http", "linkedin", "github", "+", "/"]):
                return line
    return "Unknown"


def extract_contact(text: str) -> str:
    """Extract contact information."""
    import re
    contact_lines = []
    for line in text.split("\n")[:15]:
        if any(keyword in line.lower() for keyword in ["@", "phone", "linkedin", "github", "http", "+1"]):
            contact_lines.append(line.strip())
    return " | ".join(contact_lines)


def extract_section(text: str, keywords: list) -> str:
    """Extract a section from resume based on section headers."""
    lines      = text.split("\n")
    in_section = False
    section_lines = []

    # Common next section headers to know when to stop
    all_headers = [
        "experience", "education", "skills", "projects",
        "certifications", "summary", "objective", "awards",
        "publications", "languages", "interests", "references",
        "work history", "employment", "technical skills", "profile"
    ]

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()

        # Check if this line is the section header we want
        if any(kw in line_lower for kw in keywords):
            if len(line.strip()) < 40:
                in_section = True
                continue

        # Check if we hit a new section header
        if in_section:
            is_new_header = (
                any(header in line_lower for header in all_headers)
                and len(line.strip()) < 40
                and not any(kw in line_lower for kw in keywords)
            )
            if is_new_header:
                break
            section_lines.append(line)

    return "\n".join(section_lines).strip()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 -m resume.parser <path_to_resume.pdf>")
    else:
        result = parse_resume_pdf(sys.argv[1])
        print(f"Name    : {result['name']}")
        print(f"Contact : {result['contact']}")
        print(f"\nSummary :\n{result['summary'][:200]}")
        print(f"\nSkills  :\n{result['skills'][:200]}")
        print(f"\nExperience:\n{result['experience'][:300]}")