import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import tempfile
from fetchers.all_jobs import fetch_all_jobs, SOURCES, DATE_FILTERS
from resume.parser import parse_resume_pdf
from resume.ats_scorer import calculate_ats_score, format_score_report, calculate_human_score
from resume.tuner import tune_resume, retune_resume, rehumanize_resume, save_tuned_resume

st.set_page_config(
    page_title = "JobRadar — AI Job Search & Resume Tuner",
    page_icon  = "🎯",
    layout     = "wide"
)

st.markdown("""
<style>
    .score-good { color: #28a745; font-size: 32px; font-weight: bold; }
    .score-fair { color: #ffc107; font-size: 32px; font-weight: bold; }
    .score-poor { color: #dc3545; font-size: 32px; font-weight: bold; }
    .main-header { font-size: 2.5rem; font-weight: bold; text-align: center; padding: 1rem 0; }
    .sub-header  { font-size: 1rem; color: #666; text-align: center; margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎯 JobRadar</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Job Search + Resume Tuner</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 Job Search", "📄 Resume Tuner"])

# ── US Locations ──────────────────────────────────────────────────────────────
US_LOCATIONS = [
    "USA (All States)",
    "Remote (USA)",
    "── Popular Cities ──",
    "New York, NY",
    "Los Angeles, CA",
    "Chicago, IL",
    "Houston, TX",
    "Phoenix, AZ",
    "Philadelphia, PA",
    "San Antonio, TX",
    "San Diego, CA",
    "Dallas, TX",
    "San Jose, CA",
    "Austin, TX",
    "Jacksonville, FL",
    "San Francisco, CA",
    "Seattle, WA",
    "Denver, CO",
    "Boston, MA",
    "Atlanta, GA",
    "Miami, FL",
    "Washington, DC",
    "Nashville, TN",
    "Charlotte, NC",
    "Portland, OR",
    "Las Vegas, NV",
    "Minneapolis, MN",
    "Raleigh, NC",
    "Pittsburgh, PA",
    "Richmond, VA",
    "Orlando, FL",
    "Tampa, FL",
    "Detroit, MI",
    "Baltimore, MD",
    "Louisville, KY",
    "Memphis, TN",
    "Salt Lake City, UT",
    "Columbus, OH",
    "Indianapolis, IN",
    "Kansas City, MO",
    "Oklahoma City, OK",
    "Tucson, AZ",
    "Albuquerque, NM",
    "Fresno, CA",
    "Sacramento, CA",
    "Omaha, NE",
    "Cleveland, OH",
    "Tulsa, OK",
    "Honolulu, HI",
    "Anchorage, AK",
    "── Tech Hubs ──",
    "Silicon Valley, CA",
    "Redmond, WA",
    "Cupertino, CA",
    "Mountain View, CA",
    "Palo Alto, CA",
    "Menlo Park, CA",
    "Sunnyvale, CA",
    "Santa Clara, CA",
    "San Mateo, CA",
    "Bellevue, WA",
    "Kirkland, WA",
    "Cambridge, MA",
    "Research Triangle, NC",
    "Austin Tech Corridor, TX",
    "── States ──",
    "Alabama", "Alaska", "Arizona", "Arkansas",
    "California", "Colorado", "Connecticut", "Delaware",
    "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas",
    "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma",
    "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah",
    "Vermont", "Virginia", "Washington", "West Virginia",
    "Wisconsin", "Wyoming"
]

# ── Visa Types ────────────────────────────────────────────────────────────────
VISA_TYPES = {
    "Any / No Preference": [],
    "F1 (Student Visa)":   ["f1", "student visa", "international student"],
    "OPT":                 ["opt", "optional practical training", "f1 opt"],
    "STEM OPT":            ["stem opt", "stem extension", "24 month opt"],
    "H1B":                 ["h1b", "h-1b", "h1-b", "visa sponsorship", "sponsor"],
    "Green Card / EAD":    ["green card", "ead", "permanent resident", "gc"],
    "US Citizen Only":     ["us citizen", "citizenship required", "secret clearance"]
}


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — JOB SEARCH
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Find Your Next Job")

    col1, col2 = st.columns(2)

    with col1:
        job_title = st.text_input(
            "Job Title",
            placeholder = "e.g. Machine Learning Engineer"
        )

        location = st.selectbox(
            "Location",
            options = US_LOCATIONS
        )

        experience_level = st.selectbox(
            "Experience Level",
            options = [
                "All Levels",
                "Entry Level (1-3 years)",
                "Mid Level (3-5 years)",
                "Senior Level (5+ years)"
            ]
        )

        job_type = st.multiselect(
            "Job Type",
            options = ["Full-time", "Part-time", "Contract", "Internship"],
            default = ["Full-time"]
        )

        visa_type = st.selectbox(
            "Visa Type / Work Authorization",
            options = list(VISA_TYPES.keys())
        )

    with col2:
        date_options        = {v["label"]: k for k, v in DATE_FILTERS.items()}
        selected_date_label = st.selectbox(
            "Posted Within",
            list(date_options.keys())
        )
        date_filter_key = date_options[selected_date_label]
        limit           = st.slider("Number of Jobs", 5, 100, 20, 5)

    # ── Portal checkboxes ─────────────────────────────────────────────────────
    st.subheader("Select Job Portals")
    cols     = st.columns(4)
    selected = []
    for i, key in enumerate(list(SOURCES.keys())):
        with cols[i % 4]:
            if st.checkbox(SOURCES[key]["name"], value=True, key=f"source_{key}"):
                selected.append(key)

    st.markdown("---")

    if st.button("🔍 Search Jobs", type="primary", use_container_width=True):
        if not job_title:
            st.warning("Please enter a job title.")
        elif not selected:
            st.warning("Please select at least one portal.")
        elif location.startswith("──"):
            st.warning("Please select a valid location.")
        else:
            if location in ["USA (All States)"]:
                clean_location = "USA"
            elif location == "Remote (USA)":
                clean_location = "USA"
            elif location.startswith("──"):
                clean_location = "USA"
            else:
                clean_location = location

            with st.spinner(f"Searching '{job_title}' in {location}..."):
                all_jobs = fetch_all_jobs(
                    job_title        = job_title,
                    location         = clean_location,
                    limit            = limit * 3,
                    selected_sources = selected,
                    date_filter_key  = date_filter_key
                )

                # Filter remote
                if location == "Remote (USA)":
                    remote_jobs = [j for j in all_jobs if j.get("remote", False)]
                    all_jobs    = remote_jobs if remote_jobs else all_jobs

                # Filter by experience level
                exp_map = {
                    "Entry Level (1-3 years)": [
                        "entry", "junior", "associate",
                        "jr", "grad", "graduate", "fresher"
                    ],
                    "Mid Level (3-5 years)": [
                        "mid", "intermediate", "ii",
                        "experienced", "3", "4", "5"
                    ],
                    "Senior Level (5+ years)": [
                        "senior", "sr", "lead", "principal",
                        "staff", "manager", "architect",
                        "head", "director"
                    ]
                }

                if experience_level != "All Levels":
                    keywords = exp_map.get(experience_level, [])
                    filtered = [
                        job for job in all_jobs
                        if any(
                            kw in job.get("title", "").lower() or
                            kw in job.get("description", "").lower()
                            for kw in keywords
                        )
                    ]
                    all_jobs = filtered if filtered else all_jobs

                # Filter by job type
                type_keywords = {
                    "Full-time":  ["full-time", "full time", "permanent", "fulltime"],
                    "Part-time":  ["part-time", "part time", "parttime"],
                    "Contract":   ["contract", "contractor", "freelance", "temporary"],
                    "Internship": ["intern", "internship", "co-op", "coop"]
                }

                if job_type:
                    type_filtered = []
                    for job in all_jobs:
                        combined = (
                            job.get("job_type", "").lower() + " " +
                            job.get("title", "").lower() + " " +
                            job.get("description", "")[:300].lower()
                        )
                        for sel_type in job_type:
                            if any(kw in combined for kw in type_keywords.get(sel_type, [])):
                                type_filtered.append(job)
                                break
                    all_jobs = type_filtered if type_filtered else all_jobs

                # Filter by visa type
                visa_keywords = VISA_TYPES.get(visa_type, [])
                if visa_keywords and visa_type != "Any / No Preference":
                    visa_filtered = []
                    for job in all_jobs:
                        desc = job.get("description", "").lower()
                        if any(kw in desc for kw in visa_keywords):
                            visa_filtered.append(job)
                    all_jobs = visa_filtered if visa_filtered else all_jobs

                st.session_state.search_results   = all_jobs[:limit]
                st.session_state.search_job_title = job_title
                st.session_state.search_location  = location
                st.session_state.search_exp_level = experience_level
                st.session_state.search_job_type  = job_type
                st.session_state.search_visa_type = visa_type

    # ── Show results ──────────────────────────────────────────────────────────
    if "search_results" in st.session_state:
        jobs = st.session_state.search_results

        if not jobs:
            st.error("No jobs found. Try different filters or a broader title.")
        else:
            st.success(
                f"Found **{len(jobs)}** jobs for "
                f"**{st.session_state.get('search_job_title','')}** | "
                f"📍 {st.session_state.get('search_location','')} | "
                f"👤 {st.session_state.get('search_exp_level','')} | "
                f"💼 {', '.join(st.session_state.get('search_job_type', []))} | "
                f"🛂 {st.session_state.get('search_visa_type','')}"
            )

            sources_found = {}
            for job in jobs:
                src = job.get("source", "Unknown")
                sources_found[src] = sources_found.get(src, 0) + 1

            src_cols = st.columns(len(sources_found))
            for i, (src, count) in enumerate(sources_found.items()):
                with src_cols[i]:
                    st.metric(src.split("(")[0].strip(), count)

            st.markdown("---")

            for i, job in enumerate(jobs):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{i+1}. {job.get('title', 'No Title')}**")
                    st.markdown(
                        f"🏢 {job.get('company', 'Unknown')} &nbsp;&nbsp;"
                        f"📍 {job.get('location', 'Unknown')} &nbsp;&nbsp;"
                        f"💼 {job.get('job_type', 'Full-time')} &nbsp;&nbsp;"
                        f"{'🌐 Remote' if job.get('remote') else '🏢 On-site'}"
                    )
                    salary = job.get("salary", "")
                    if salary and salary != "Not specified":
                        st.markdown(f"💰 {salary}")
                    posted = job.get("posted_at", "")
                    if posted:
                        st.markdown(
                            f"📅 {posted[:10]} &nbsp;&nbsp;"
                            f"🔗 {job.get('source', '')}"
                        )
                with c2:
                    url = job.get("url", "")
                    if url:
                        st.link_button("Apply Now", url, use_container_width=True)
                    if st.button("Tune Resume", key=f"tune_{i}", use_container_width=True):
                        st.session_state.selected_job = job
                        st.info("Go to the Resume Tuner tab!")
                st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — RESUME TUNER
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("AI Resume Tuner")
    st.markdown("Upload your resume and paste a job description to get an ATS-optimized resume.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Upload Your Resume")
        uploaded_file = st.file_uploader(
            "Drag and drop or click to upload your resume PDF",
            type = ["pdf"]
        )
        if uploaded_file:
            st.success(f"Resume uploaded: {uploaded_file.name}")

        job_title_tune = st.text_input(
            "Job Title",
            placeholder = "e.g. Junior AI/ML Engineer",
            key         = "tune_job_title"
        )

        if "selected_job" in st.session_state:
            job = st.session_state.selected_job
            st.info(f"Selected: {job.get('title')} at {job.get('company')}")

    with col2:
        st.subheader("Paste Job Description")
        default_jd = ""
        if "selected_job" in st.session_state:
            default_jd = st.session_state.selected_job.get("description", "")

        job_description = st.text_area(
            "Paste the full job description here",
            value  = default_jd,
            height = 300
        )

    st.markdown("---")

    # ── Tune button ───────────────────────────────────────────────────────────
    if st.button("🚀 Tune My Resume", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload your resume PDF first.")
        elif not job_description:
            st.error("Please paste the job description.")
        elif not job_title_tune:
            st.error("Please enter the job title.")
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                with st.spinner("Reading your resume..."):
                    resume_data = parse_resume_pdf(tmp_path)
                    resume_text = resume_data["full_text"]

                score_before = calculate_ats_score(resume_text, job_description)

                with st.spinner("AI is rewriting your resume... (30-60 seconds)"):
                    result = tune_resume(resume_text, job_description, job_title_tune)

                if "error" not in result:
                    st.session_state.tune_score_before = score_before
                    st.session_state.tune_result       = result
                    st.session_state.tune_jd           = job_description
                    st.session_state.tune_title        = job_title_tune
                    st.session_state.retune_resume     = result["tuned_resume"]
                    st.session_state.retune_score      = result["score_after"]["total_score"]
                    st.session_state.retune_round      = 1
                    if "retune_result" in st.session_state:
                        del st.session_state.retune_result
                    if "human_result" in st.session_state:
                        del st.session_state.human_result
                else:
                    st.error(f"Error: {result['error']}")
            finally:
                os.unlink(tmp_path)

    # ── Show tune results ─────────────────────────────────────────────────────
    if "tune_result" in st.session_state:
        result       = st.session_state.tune_result
        score_before = st.session_state.tune_score_before
        score_after  = result["score_after"]
        score_val    = score_before["total_score"]
        score_val2   = score_after["total_score"]

        # Score BEFORE
        color = "score-good" if score_val >= 75 else "score-fair" if score_val >= 50 else "score-poor"
        st.markdown("### ATS Score — Before Tuning")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="{color}">{score_val}/100</div>', unsafe_allow_html=True)
            st.progress(score_val / 100)
        with col2:
            st.metric("Keywords Matched", f"{score_before['matched_count']}/{score_before['total_jd_keywords']}")
            st.metric("Skills Score",     f"{score_before['skills_score']}/25")
        with col3:
            st.metric("Experience Score", f"{score_before['exp_score']}/20")
            st.metric("Education Score",  f"{score_before['edu_score']}/10")

        if score_before.get("missing_skills"):
            st.warning(f"Missing skills: {', '.join(score_before['missing_skills'][:5])}")

        st.markdown("---")

        # Score AFTER
        color2 = "score-good" if score_val2 >= 75 else "score-fair" if score_val2 >= 50 else "score-poor"
        st.markdown("### ATS Score — After Tuning")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="{color2}">{score_val2}/100</div>', unsafe_allow_html=True)
            st.progress(score_val2 / 100)
        with col2:
            st.metric(
                "Keywords Matched",
                f"{score_after['matched_count']}/{score_after['total_jd_keywords']}",
                delta = score_after['matched_count'] - score_before['matched_count']
            )
            st.metric(
                "Skills Score",
                f"{score_after['skills_score']}/25",
                delta = score_after['skills_score'] - score_before['skills_score']
            )
        with col3:
            st.metric("Total Improvement", f"+{score_val2 - score_val}", delta=score_val2 - score_val)
            st.metric("Final Score", f"{score_val2}/100")

        st.markdown("---")

        # Show tuned resume
        st.markdown("### Your Updated Resume")
        st.text_area(
            "Copy this resume",
            value  = result["tuned_resume"],
            height = 400,
            key    = "tuned_text"
        )

        # Download PDF
        pdf_path = save_tuned_resume(result["tuned_resume"])
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label               = "📥 Download Tuned Resume as PDF",
            data                = pdf_bytes,
            file_name           = "tuned_resume.pdf",
            mime                = "application/pdf",
            use_container_width = True
        )

        with st.expander("📊 View Full ATS Report"):
            st.markdown(result["final_report"])

        st.markdown("---")

        # ── Human vs AI Writing Score ─────────────────────────────────────────
        st.markdown("### ✍️ Human vs AI Writing Score")
        human_data = calculate_human_score(result["tuned_resume"])

        col1, col2, col3 = st.columns(3)
        with col1:
            h_color = "score-good" if human_data["human_score"] >= 90 else \
                      "score-fair" if human_data["human_score"] >= 75 else "score-poor"
            st.markdown(
                f'<div class="{h_color}">🧑 Human: {human_data["human_score"]}%</div>',
                unsafe_allow_html=True
            )
            st.progress(human_data["human_score"] / 100)
        with col2:
            a_color = "score-poor" if human_data["ai_score"] >= 25 else \
                      "score-fair" if human_data["ai_score"] >= 10 else "score-good"
            st.markdown(
                f'<div class="{a_color}">🤖 AI: {human_data["ai_score"]}%</div>',
                unsafe_allow_html=True
            )
            st.progress(human_data["ai_score"] / 100)
        with col3:
            st.markdown(f"**{human_data['emoji']} {human_data['rating']}**")
            if human_data["ai_phrases_found"]:
                st.warning(
                    f"AI phrases detected: "
                    f"{', '.join(human_data['ai_phrases_found'][:5])}"
                )

        if human_data["human_score"] < 95:
            st.warning(
                f"Human writing score is {human_data['human_score']}%. "
                f"Click below to rewrite in natural human language — "
                f"all content and meaning stays exactly the same."
            )
            if st.button(
                "✍️ Re-write in Human Tone",
                type                = "primary",
                use_container_width = True,
                key                 = "rehumanize_btn"
            ):
                with st.spinner("Rewriting resume in natural human tone... (30-60 seconds)"):
                    human_result = rehumanize_resume(
                        resume_text     = result["tuned_resume"],
                        job_description = st.session_state.tune_jd,
                        job_title       = st.session_state.tune_title
                    )

                if "error" not in human_result:
                    st.session_state.human_result  = human_result
                    st.session_state.retune_resume = human_result["human_resume"]
                else:
                    st.error(f"Error: {human_result['error']}")
        else:
            st.success(
                f"✅ Human score: {human_data['human_score']}% — "
                f"Resume sounds naturally written! No rewrite needed."
            )

        # Show human rewrite result
        if "human_result" in st.session_state:
            hr       = st.session_state.human_result
            h_after  = hr["score_after"]["human_score"]
            h_before = hr["score_before"]["human_score"]
            ai_after = hr["score_after"]["ai_score"]

            st.markdown("---")
            st.markdown("### ✅ Re-written in Human Tone")

            col1, col2, col3 = st.columns(3)
            with col1:
                color_h = "score-good" if h_after >= 90 else "score-fair"
                st.markdown(
                    f'<div class="{color_h}">🧑 Human: {h_after}%</div>',
                    unsafe_allow_html=True
                )
                st.progress(h_after / 100)
            with col2:
                color_a = "score-good" if ai_after <= 10 else "score-fair"
                st.markdown(
                    f'<div class="{color_a}">🤖 AI: {ai_after}%</div>',
                    unsafe_allow_html=True
                )
                st.progress(ai_after / 100)
            with col3:
                st.metric(
                    "Human Score Improvement",
                    f"{h_after}%",
                    delta = h_after - h_before
                )

            st.markdown("#### Your Human-Written Resume")
            st.text_area(
                "Copy this resume",
                value  = hr["human_resume"],
                height = 400,
                key    = "human_text"
            )

            human_pdf = save_tuned_resume(
                hr["human_resume"],
                output_path = "human_resume.pdf"
            )
            with open(human_pdf, "rb") as f:
                human_bytes = f.read()

            st.download_button(
                label               = "📥 Download Human-Written Resume as PDF",
                data                = human_bytes,
                file_name           = "human_resume.pdf",
                mime                = "application/pdf",
                use_container_width = True
            )

            with st.expander("📊 View Human Writing Report"):
                st.markdown(hr["human_report"])

            if h_after >= 95:
                st.success(
                    f"🎉 Human score: {h_after}% — "
                    f"Resume sounds completely natural and ready to submit!"
                )
            else:
                st.warning(
                    f"Human score is {h_after}%. "
                    f"Click Re-write again to push higher!"
                )
                if st.button(
                    "✍️ Re-write Again for Higher Human Score",
                    type                = "primary",
                    use_container_width = True,
                    key                 = "rehumanize_again_btn"
                ):
                    with st.spinner("Rewriting again in human tone..."):
                        next_human = rehumanize_resume(
                            resume_text     = hr["human_resume"],
                            job_description = st.session_state.tune_jd,
                            job_title       = st.session_state.tune_title
                        )
                    if "error" not in next_human:
                        st.session_state.human_result  = next_human
                        st.session_state.retune_resume = next_human["human_resume"]
                        st.rerun()

        st.markdown("---")

        # ── Re-tune section ───────────────────────────────────────────────────
        current_score = st.session_state.retune_score

        if current_score >= 95:
            st.balloons()
            st.success(
                f"🎉 Perfect! Your resume scores {current_score}/100 — "
                f"ATS Optimized and ready to submit!"
            )
            st.info("Download your resume above and submit with confidence!")
        else:
            st.warning(
                f"Your ATS score is {current_score}/100. "
                f"Click Re-tune to target missing requirements and push above 95%+"
            )

            if st.button(
                "🔄 Re-tune Resume for Higher ATS Score",
                type                = "primary",
                use_container_width = True
            ):
                with st.spinner("Analyzing ATS report and targeting missing requirements..."):
                    retune_result = retune_resume(
                        tuned_resume_text = st.session_state.retune_resume,
                        job_description   = st.session_state.tune_jd,
                        job_title         = st.session_state.tune_title,
                        previous_score    = current_score
                    )

                if "error" not in retune_result:
                    st.session_state.retune_result = retune_result
                    st.session_state.retune_resume = retune_result["tuned_resume"]
                    st.session_state.retune_score  = retune_result["score_after"]["total_score"]
                    st.session_state.retune_round  = st.session_state.get("retune_round", 1) + 1

    # ── Show re-tune results ──────────────────────────────────────────────────
    if "retune_result" in st.session_state:
        retune_result = st.session_state.retune_result
        new_score     = retune_result["score_after"]["total_score"]
        old_score     = retune_result["score_before"]["total_score"]
        round_num     = st.session_state.get("retune_round", 1)

        st.markdown(f"### Re-tune Round {round_num} — ATS Score")
        col1, col2 = st.columns(2)
        with col1:
            color3 = "score-good" if new_score >= 75 else "score-fair"
            st.markdown(f'<div class="{color3}">{new_score}/100</div>', unsafe_allow_html=True)
            st.progress(new_score / 100)
        with col2:
            st.metric(
                "Score Improvement",
                f"{new_score}/100",
                delta = new_score - old_score
            )

        st.markdown("### Re-tuned Resume")
        st.text_area(
            "Copy this improved resume",
            value  = retune_result["tuned_resume"],
            height = 400,
            key    = f"retune_text_{round_num}"
        )

        retune_pdf = save_tuned_resume(
            retune_result["tuned_resume"],
            output_path = "retuned_resume.pdf"
        )
        with open(retune_pdf, "rb") as f:
            retune_bytes = f.read()
        st.download_button(
            label               = "📥 Download Re-tuned Resume as PDF",
            data                = retune_bytes,
            file_name           = "retuned_resume.pdf",
            mime                = "application/pdf",
            use_container_width = True,
            key                 = f"download_retune_{round_num}"
        )

        with st.expander("📊 View Re-tune Report — What Was Fixed"):
            score_data = retune_result["score_before"]
            st.markdown("### What the AI targeted this round:")
            if score_data.get("missing_keywords"):
                st.markdown("**Missing keywords that were added:**")
                st.write(", ".join(score_data["missing_keywords"][:15]))
            if score_data.get("missing_skills"):
                st.markdown("**Missing skills that were added:**")
                st.write(", ".join(score_data["missing_skills"]))
            st.markdown("---")
            st.markdown(retune_result["final_report"])

        st.markdown("---")

        if new_score >= 95:
            st.balloons()
            st.success(
                f"🎉 Perfect! Your resume now scores {new_score}/100 — "
                f"Fully optimized and ready to submit!"
            )
        else:
            st.warning(
                f"Score is now {new_score}/100. "
                f"Click Re-tune again to push higher!"
            )
            if st.button(
                "🔄 Re-tune Again for Even Higher Score",
                type                = "primary",
                use_container_width = True,
                key                 = f"retune_again_{round_num}"
            ):
                with st.spinner("Re-tuning again targeting remaining gaps..."):
                    next_retune = retune_resume(
                        tuned_resume_text = st.session_state.retune_resume,
                        job_description   = st.session_state.tune_jd,
                        job_title         = st.session_state.tune_title,
                        previous_score    = new_score
                    )

                if "error" not in next_retune:
                    st.session_state.retune_result = next_retune
                    st.session_state.retune_resume = next_retune["tuned_resume"]
                    st.session_state.retune_score  = next_retune["score_after"]["total_score"]
                    st.session_state.retune_round  = round_num + 1
                    st.rerun()