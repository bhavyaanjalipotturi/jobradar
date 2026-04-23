import re
from collections import Counter

def calculate_ats_score(resume_text: str, job_description: str) -> dict:
    """
    Calculates ATS match score between resume and job description.
    Returns score breakdown and missing keywords.
    """

    def clean_text(text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return text

    def extract_keywords(text: str) -> set:
        clean    = clean_text(text)
        words    = clean.split()
        # Remove common stop words
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "is", "are",
            "was", "were", "be", "been", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may",
            "might", "must", "shall", "this", "that", "these", "those",
            "i", "you", "he", "she", "we", "they", "it", "its",
            "your", "our", "their", "my", "his", "her", "as", "not",
            "what", "which", "who", "whom", "when", "where", "why", "how"
        }
        return {w for w in words if w not in stopwords and len(w) > 2}

    def extract_phrases(text: str) -> set:
        """Extract 2-3 word phrases."""
        clean  = clean_text(text)
        words  = clean.split()
        phrases = set()
        for i in range(len(words) - 1):
            phrases.add(f"{words[i]} {words[i+1]}")
        for i in range(len(words) - 2):
            phrases.add(f"{words[i]} {words[i+1]} {words[i+2]}")
        return phrases

    resume_lower = resume_text.lower()
    jd_lower     = job_description.lower()

    # Extract keywords and phrases
    jd_keywords     = extract_keywords(job_description)
    resume_keywords = extract_keywords(resume_text)
    jd_phrases      = extract_phrases(job_description)

    # --- Scoring categories ---

    # 1. Keyword match (30 points)
    matched_keywords = jd_keywords.intersection(resume_keywords)
    missing_keywords = jd_keywords - resume_keywords
    keyword_score    = min(30, int((len(matched_keywords) / max(len(jd_keywords), 1)) * 30))

    # 2. Skills match (25 points)
    tech_skills = {
        "python", "java", "javascript", "typescript", "sql", "nosql",
        "react", "node", "fastapi", "flask", "django", "aws", "gcp",
        "azure", "docker", "kubernetes", "git", "tensorflow", "pytorch",
        "langchain", "openai", "anthropic", "machine learning", "deep learning",
        "nlp", "llm", "api", "rest", "graphql", "postgresql", "mongodb",
        "redis", "spark", "hadoop", "tableau", "powerbi", "excel",
        "scikit-learn", "pandas", "numpy", "streamlit", "fastapi",
        "langraph", "llamaindex", "chromadb", "pinecone", "weaviate",
        "mlflow", "airflow", "dbt", "snowflake", "databricks"
    }
    jd_skills     = jd_keywords.intersection(tech_skills)
    resume_skills = resume_keywords.intersection(tech_skills)
    matched_skills = jd_skills.intersection(resume_skills)
    missing_skills = jd_skills - resume_skills
    skills_score   = min(25, int((len(matched_skills) / max(len(jd_skills), 1)) * 25))

    # 3. Experience relevance (20 points)
    exp_keywords = {
        "experience", "years", "senior", "junior", "lead", "manager",
        "engineer", "developer", "analyst", "scientist", "architect",
        "intern", "associate", "principal", "staff", "director"
    }
    jd_exp     = jd_keywords.intersection(exp_keywords)
    resume_exp = resume_keywords.intersection(exp_keywords)
    exp_score  = min(20, int((len(jd_exp.intersection(resume_exp)) / max(len(jd_exp), 1)) * 20))

    # 4. Education match (10 points)
    edu_keywords = {
        "bachelor", "master", "phd", "degree", "computer science",
        "engineering", "mathematics", "statistics", "data science",
        "bs", "ms", "mba", "btech", "mtech"
    }
    jd_edu     = jd_keywords.intersection(edu_keywords)
    resume_edu = resume_keywords.intersection(edu_keywords)
    edu_score  = min(10, int((len(jd_edu.intersection(resume_edu)) / max(len(jd_edu), 1)) * 10))

    # 5. Job title match (10 points)
    title_keywords = jd_lower.split("\n")[0].lower().split()
    title_score    = 0
    for word in title_keywords:
        if word in resume_lower and len(word) > 3:
            title_score += 2
    title_score = min(10, title_score)

    # 6. Format/readability (5 points)
    format_score = 0
    if len(resume_text) > 200:  format_score += 1
    if len(resume_text) > 500:  format_score += 1
    if "\n" in resume_text:     format_score += 1
    if len(resume_text) < 5000: format_score += 2

    # Total score
    total_score = (
        keyword_score +
        skills_score  +
        exp_score     +
        edu_score     +
        title_score   +
        format_score
    )

    # Top missing keywords to add
    top_missing = sorted(list(missing_keywords))[:20]
    top_missing_skills = sorted(list(missing_skills))[:10]

    return {
        "total_score":        total_score,
        "keyword_score":      keyword_score,
        "skills_score":       skills_score,
        "exp_score":          exp_score,
        "edu_score":          edu_score,
        "title_score":        title_score,
        "format_score":       format_score,
        "matched_keywords":   sorted(list(matched_keywords))[:20],
        "missing_keywords":   top_missing,
        "missing_skills":     top_missing_skills,
        "total_jd_keywords":  len(jd_keywords),
        "matched_count":      len(matched_keywords),
    }


def format_score_report(score_data: dict, label: str = "ATS Score") -> str:
    """Format the score report for display."""
    total = score_data["total_score"]

    if total >= 90:
        rating = "EXCELLENT"
        emoji  = "🟢"
    elif total >= 75:
        rating = "GOOD"
        emoji  = "🟡"
    elif total >= 50:
        rating = "FAIR"
        emoji  = "🟠"
    else:
        rating = "POOR"
        emoji  = "🔴"

    report = f"""
{emoji} {label}: {total}/100 — {rating}
{'=' * 50}
Keyword Match    : {score_data['keyword_score']}/30
Skills Match     : {score_data['skills_score']}/25
Experience       : {score_data['exp_score']}/20
Education        : {score_data['edu_score']}/10
Job Title Match  : {score_data['title_score']}/10
Format           : {score_data['format_score']}/5
{'=' * 50}
Keywords matched : {score_data['matched_count']} / {score_data['total_jd_keywords']}
Missing keywords : {', '.join(score_data['missing_keywords'][:10])}
Missing skills   : {', '.join(score_data['missing_skills'][:5])}
"""
    return report