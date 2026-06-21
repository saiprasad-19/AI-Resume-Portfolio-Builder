import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import io
import re
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ============================================================
# UI ENHANCEMENT — Page configuration
# Switches to a wide layout so the form can sit next to an
# illustration panel like a typical SaaS product page.
# No functionality is affected by this call.
# ============================================================
st.set_page_config(
    page_title="AI Resume & Portfolio Builder",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# UI ENHANCEMENT — Global dark "SaaS product" theme
# Everything in this CSS block only restyles existing Streamlit
# elements (inputs, buttons, forms, alerts, sidebar). It does not
# add, remove, or change any logic. The original rule that hides
# the "Press Enter to apply" input hint is preserved at the bottom.
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Page background: deep charcoal with soft accent glows */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 15% 0%, rgba(99,102,241,0.10), transparent 40%),
        radial-gradient(circle at 85% 100%, rgba(34,211,238,0.08), transparent 40%),
        #0b0d14;
}

/* Hide default Streamlit chrome for a cleaner product look */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #11141f;
    border-right: 1px solid #232739;
}
[data-testid="stSidebar"] * { color: #d1d5db; }

/* Hero header */
.hero { text-align: center; padding: 1.4rem 1rem 1.8rem 1rem; }
.hero-badge {
    display: inline-block;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #ffffff;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    margin-bottom: 0.9rem;
    letter-spacing: 0.02em;
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    margin: 0.2rem 0 0.6rem 0;
    background: linear-gradient(90deg, #f9fafb, #c7d2fe);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.hero-subtitle {
    color: #9ca3af;
    font-size: 1.05rem;
    max-width: 640px;
    margin: 0 auto 1.1rem auto;
}
.hero-pills { display: flex; justify-content: center; gap: 0.5rem; flex-wrap: wrap; }
.pill {
    background: #161a26;
    border: 1px solid #2a2f45;
    color: #d1d5db;
    padding: 0.35rem 0.9rem;
    border-radius: 999px;
    font-size: 0.85rem;
}

/* Small uppercase labels used above generated results */
.section-kicker {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.78rem;
    font-weight: 700;
    color: #8b8fa3;
    margin-bottom: -0.3rem;
}

/* Form card */
[data-testid="stForm"] {
    background: #141826;
    border: 1px solid #262b3d;
    border-radius: 18px;
    padding: 1.6rem 1.6rem 0.8rem 1.6rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}

/* Inputs */
.stTextInput input, .stTextArea textarea {
    background: #0f1320 !important;
    color: #e5e7eb !important;
    border: 1px solid #2a2f45 !important;
    border-radius: 10px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 1px #8b5cf6 !important;
}
[data-testid="stWidgetLabel"] p {
    color: #c7cad1 !important;
    font-weight: 500;
    font-size: 0.92rem;
}

/* Buttons: form-submit buttons + the PDF download button */
div[data-testid="stForm"] button,
.stDownloadButton button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.55rem 1rem !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35);
}
div[data-testid="stForm"] button:hover,
.stDownloadButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(139,92,246,0.45);
}

/* Success / info alert boxes */
[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Illustration + feature panel beside the form */
.illustration-panel {
    background: #141826;
    border: 1px solid #262b3d;
    border-radius: 18px;
    padding: 1.2rem 1.2rem 1.4rem 1.2rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}
.illustration-panel svg { width: 100%; height: auto; display: block; }
.feature-list { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.55rem; }
.feature-item {
    color: #d1d5db;
    font-size: 0.92rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.feature-icon { font-size: 1rem; }

/* Original behavior, preserved: hide the "Press Enter to apply" hint */
[data-testid="InputInstructions"] { display: none; }

/* Responsive tweaks for narrow screens */
@media (max-width: 900px) {
    .hero-title { font-size: 1.8rem; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# UI ENHANCEMENT — Hero header
# Same title and description text as the original app, restyled
# as a centered hero section with a "powered by" badge and
# feature pills instead of a plain st.title() + st.markdown().
# ============================================================
st.markdown("""
<div class="hero">
  <div class="hero-badge">⚡ Powered by Groq + Llama 3</div>
  <h1 class="hero-title">🚀 AI-Powered Resume &amp; Portfolio Builder</h1>
  <p class="hero-subtitle">
    Generate professional resumes, cover letters and portfolio content
    using Generative AI.
  </p>
  <div class="hero-pills">
    <span class="pill">📄 Resume</span>
    <span class="pill">✉️ Cover Letter</span>
    <span class="pill">🌐 Portfolio</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("🚀 AI-Powered Resume & Portfolio Builder")

st.sidebar.info(
    """
    AI Resume & Portfolio Builder
    
    Features:
    - Resume Generation
    - Cover Letter Generation
    - Portfolio Generation
    
    Powered by Groq + Llama 3
    """
)

# if st.button("Test AI"):

#     response = client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=[
#             {
#                 "role": "user",
#                 "content": "Write a professional summary for a Computer Science student."
#             }
#         ]
#     )

#     st.write(response.choices[0].message.content)

# ============================================================
# UI ENHANCEMENT — Two-column layout: form (left) + illustration
# and feature highlights (right). The form itself below is
# 100% identical to the original: same fields, same order, same
# labels/placeholders, same three buttons assigned to the same
# variable names (resume_btn, cover_btn, portfolio_btn).
# ============================================================
col_form, col_illustration = st.columns([1.4, 1], gap="large")

with col_form:
    st.markdown('<p class="section-kicker">📝 Fill in your details</p>', unsafe_allow_html=True)

    with st.form("resume_form"):

        name = st.text_input("Full Name")

        email = st.text_input("Email")

        phone = st.text_input("Phone Number")

        location = st.text_input("Location")

        github = st.text_input("GitHub Profile")

        linkedin = st.text_input("LinkedIn Profile")

        education = st.text_area("Education")

        skills = st.text_area(
            "Skills",
            placeholder="Python, Java, Machine Learning, React..."
        )

        projects = st.text_area(
            "Projects",
            placeholder="Describe your projects..."
        )

        certifications = st.text_area("Certifications")

        career_goal = st.text_area("Career Goal")

        col1, col2, col3 = st.columns(3)

        with col1:
            resume_btn = st.form_submit_button("Generate Resume")

        with col2:
            cover_btn = st.form_submit_button("Generate Cover Letter")

        with col3:
            portfolio_btn = st.form_submit_button("Generate Portfolio")

with col_illustration:

    st.image("resume_ai.png", width=300)

    st.markdown("""
    ### Why Use This Tool?

    ✅ ATS-Friendly Resume

    ✅ AI Generated Cover Letter

    ✅ Portfolio Content Generator

    ✅ One-Click PDF Download
    """)

if resume_btn:

    prompt = f"""
    Create a professional ATS-friendly resume using the information below.

    Name: {name}
    Email: {email}
    Phone Number: {phone}
    Location: {location}

    GitHub: {github}
    LinkedIn: {linkedin}

    Education:
    {education}

    Skills:
    {skills}

    Projects:
    {projects}

    Certifications:
    {certifications}

    Career Goal:
    {career_goal}

    Return the resume using EXACTLY this structure. Use the section markers
    exactly as written (including the ### symbols) and nothing else around them:

    ###SUMMARY###
    (A 3-4 sentence professional summary)

    ###EDUCATION###
    (One clean line per degree/institution, most recent first)

    ###SKILLS###
    (A clean comma-separated list of skills)

    ###PROJECTS###

    For each project, use EXACTLY this format:

    PROJECT: Project Name

    - Bullet 1
    - Bullet 2
    - Bullet 3

    PROJECT: Next Project Name

    - Bullet 1
    - Bullet 2
    - Bullet 3

    IMPORTANT:
    - Every project MUST start with PROJECT:
    - Never put project names inside bullets.
    - Never merge two projects.
    - Never create new projects.
    - Keep the exact project names provided by the user.
    - Generate bullets only from the information provided by the user.
    - If multiple projects are provided, create separate PROJECT sections for each one.

    ###CERTIFICATIONS###
    - <certification 1>
    - <certification 2>

    ###OBJECTIVE###
    (A 2-3 sentence career objective)

    Rules:
    - Do not write any text before ###SUMMARY### or after the career objective.
    - Do not use markdown symbols like **, ##, or ---.
    - Do not use tables.
    - Keep bullet points concise and achievement-oriented.
    - Make it suitable for internships and placements.
    - Keep it ATS-friendly.
     """
    with st.spinner("Generating Resume..."):

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

    st.divider()
    st.markdown('<p class="section-kicker">📄 Result</p>', unsafe_allow_html=True)
    st.subheader("Generated Resume")
    st.success("Resume Generated Successfully!")

    resume_text = response.choices[0].message.content

    resume_text = (
        resume_text
        .replace("•", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("**", "")
    )

    # Hide the ### section markers in the on-screen preview only.
    # The raw resume_text (with markers) is still used by the PDF builder below.
    preview_text = re.sub(r"###[A-Z]+###", "", resume_text).strip()
    st.write(preview_text)
    # ---------- Parse the structured resume text into sections ----------
    def parse_resume_sections(text):
        pattern = r"###(SUMMARY|EDUCATION|SKILLS|PROJECTS|CERTIFICATIONS|OBJECTIVE)###"
        parts = re.split(pattern, text)
        parsed = {}
        it = iter(parts[1:])
        for key, content in zip(it, it):
            parsed[key] = content.strip()
        return parsed

    def parse_projects(projects_text):
        items = []
        current = None
        for raw_line in projects_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.upper().startswith("PROJECT:"):
                if current:
                    items.append(current)
                current = {"title": line.split(":", 1)[1].strip(), "bullets": []}
            elif line.startswith("-"):
                if current:
                    current["bullets"].append(line.lstrip("-").strip())
            else:
                if current:
                    current["bullets"].append(line)
                else:
                    current = {"title": line, "bullets": []}
        if current:
            items.append(current)
        return items

    def parse_bullet_list(text):
        items = []
        for raw_line in text.splitlines():
            line = raw_line.strip().lstrip("-").strip()
            if line:
                items.append(line)
        return items

    sections = parse_resume_sections(resume_text)

    # ---------- Build the PDF with ReportLab ----------
    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "NameStyle", parent=styles["Title"],
        fontSize=20, alignment=TA_CENTER, spaceAfter=2,
        textColor=colors.HexColor("#1a1a1a")
    )
    contact_style = ParagraphStyle(
        "ContactStyle", parent=styles["Normal"],
        fontSize=10, alignment=TA_CENTER,
        textColor=colors.HexColor("#444444"), spaceAfter=10
    )
    heading_style = ParagraphStyle(
        "HeadingStyle", parent=styles["Heading2"],
        fontSize=12, spaceBefore=8, spaceAfter=4,
        textColor=colors.HexColor("#1a1a1a")
    )
    body_style = ParagraphStyle(
        "BodyStyle", parent=styles["Normal"],
        fontSize=10.5, leading=14, spaceAfter=4
    )
    bullet_style = ParagraphStyle(
        "BulletStyle", parent=styles["Normal"],
        fontSize=10.5, leading=14, leftIndent=14, spaceAfter=2
    )
    project_title_style = ParagraphStyle(
        "ProjectTitleStyle", parent=styles["Normal"],
        fontSize=10.5, leading=14, spaceBefore=4, spaceAfter=2,
        fontName="Helvetica-Bold"
    )

    def safe(text):
        return xml_escape(text or "")

    def section_heading(title):
        return [
            Paragraph(safe(title).upper(), heading_style),
            HRFlowable(width="100%", thickness=0.8,
                       color=colors.HexColor("#999999"), spaceAfter=6),
        ]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=LETTER,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch
    )

    story = []
    story.append(Paragraph(safe(name), name_style))
    contact_info = (
        f"<b>Location:</b> {location}"
        f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<b>Phone:</b> {phone}"
        f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<b>Email:</b> {email}"
    )

    if github:
        contact_info += (
            f'<br/><b>GitHub:</b> '
            f'<font color="blue">{github}</font>'
        )

    if linkedin:
        linkedin_display = linkedin.replace("https://www.", "").replace("https://", "")

        contact_info += (
            f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            f'<b>LinkedIn:</b> '
            f'<font color="blue">{linkedin_display}</font>'
        )

    story.append(Paragraph(contact_info, contact_style))
    summary_text = sections.get("SUMMARY", "").strip()
    if summary_text:
        story += section_heading("Professional Summary")
        story.append(Paragraph(safe(summary_text), body_style))

    education_text = sections.get("EDUCATION", "").strip() or education
    if education_text:
        story += section_heading("Education")
        for line in education_text.splitlines():
            line = line.strip()
            if line:
                story.append(Paragraph(safe(line), body_style))

    skills_text = sections.get("SKILLS", "").strip() or skills
    if skills_text:
        story += section_heading("Technical Skills")
        story.append(Paragraph(safe(skills_text.replace(chr(10), ", ")), body_style))

    projects_list = parse_projects(sections.get("PROJECTS", "").strip())
    if not projects_list and projects.strip():
        projects_list = [{"title": projects.strip(), "bullets": []}]
    if projects_list:
        story += section_heading("Projects")
        for proj in projects_list:
            if proj.get("title"):
                story.append(Paragraph(safe(proj["title"]), project_title_style))
            for bullet in proj.get("bullets", []):
                story.append(Paragraph(f"\u2022 {safe(bullet)}", bullet_style))

    cert_items = parse_bullet_list(sections.get("CERTIFICATIONS", "").strip())
    if not cert_items and certifications.strip():
        cert_items = [c.strip() for c in certifications.splitlines() if c.strip()]
    if cert_items:
        story += section_heading("Certifications")
        for cert in cert_items:
            story.append(Paragraph(f"\u2022 {safe(cert)}", bullet_style))

    objective_text = sections.get("OBJECTIVE", "").strip() or career_goal
    if objective_text:
        story += section_heading("Career Objective")
        story.append(Paragraph(safe(objective_text), body_style))

    doc.build(story)
    buffer.seek(0)

    st.download_button(
        label="📥 Download Resume PDF",
        data=buffer,
        file_name="resume.pdf",
        mime="application/pdf"
    )
if cover_btn:

    prompt = f"""
    Write a professional internship/job cover letter.

    Student Name: {name}
    Education: {education}
    Skills: {skills}
    Projects: {projects}
    Certifications: {certifications}
    Career Goal: {career_goal}

    Requirements:
    - Address it to "Hiring Manager"
    - Do not use placeholders like [Company Name] or [Address]
    - Use the actual student information provided
    - Mention projects and skills naturally
    - Keep it professional and ATS-friendly
    - End with the student's name
    """

    with st.spinner("Generating Cover Letter..."):

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
    st.divider()
    st.markdown('<p class="section-kicker">✉️ Result</p>', unsafe_allow_html=True)
    st.subheader("Generated Cover Letter")
    st.success("Cover Letter Generated Successfully!")

    st.write(response.choices[0].message.content)
if portfolio_btn:

    prompt = f"""
    Create professional portfolio content for a student.

    Name: {name}
    Education: {education}
    Skills: {skills}
    Projects: {projects}
    Certifications: {certifications}
    Career Goal: {career_goal}

    Create the following sections:

    1. About Me
    2. Skills Overview
    3. Featured Projects
    4. Certifications
    5. Career Objective

    Rules:
    - Use the actual student information.
    - Do not use placeholders.
    - Make it professional.
    - Make it suitable for a personal portfolio website.
    """

    with st.spinner("Generating Portfolio Content..."):

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

    st.divider()
    st.markdown('<p class="section-kicker">🌐 Result</p>', unsafe_allow_html=True)
    st.subheader("Generated Portfolio Content")
    st.success("Portfolio Content Generated Successfully!")

    st.write(response.choices[0].message.content)