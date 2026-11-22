import os
import re
import time
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from google import genai
from docx import Document
from docx.shared import Pt

load_dotenv()

st.set_page_config(
    page_title="Syllabus-to-Notes Generator",
    page_icon="📚",
    layout="wide"
)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def split_syllabus_by_unit(syllabus: str):
    """
    Split syllabus text using headings such as:
    UNIT I, UNIT 1, Unit-2, MODULE III, Module 4.
    The heading is included in each returned unit.
    """
    heading_pattern = re.compile(
        r"^\s*(?:UNIT|MODULE)\s*[-:]?\s*(?:[IVXLCDM]+|\d+)\b.*$",
        flags=re.IGNORECASE | re.MULTILINE
    )

    matches = list(heading_pattern.finditer(syllabus))
    if not matches:
        return []

    units = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(syllabus)
        unit_text = syllabus[start:end].strip()
        if unit_text:
            units.append(unit_text)

    return units


def generate_unit_notes(client, unit_text, detail_level, audience):

    prompt = f"""
    You are an experienced university lecturer.

    Generate organised, easy-to-understand study notes
    based on the following syllabus unit.

    Preserve all topics and subtopics.
    Include definitions, explanations and examples.
    Use headings, subheadings and bullet points.
    End with a Quick Revision section.

    Detail level: {detail_level}
    Target audience: {audience}

    Syllabus:
    {unit_text}
    """

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            if not response.text:
                raise ValueError("Empty response from Gemini")

            return response.text.strip()

        except Exception as error:
            if attempt == 2:
                raise

            wait_time = 2 ** (attempt + 1)
            st.warning(
                f"Gemini is temporarily unavailable. "
                f"Retrying in {wait_time} seconds..."
            )
            time.sleep(wait_time)


def markdown_to_docx(markdown_text: str, title: str):
    doc = Document()
    doc.add_heading(title, level=0)

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith(("- ", "* ")):
            doc.add_paragraph(line[2:], style="List Bullet")
        elif re.match(r"^\d+[\.)]\s+", line):
            content = re.sub(r"^\d+[\.)]\s+", "", line)
            doc.add_paragraph(content, style="List Number")
        else:
            paragraph = doc.add_paragraph()
            # Basic bold-markdown support for **text**.
            parts = re.split(r"(\*\*.*?\*\*)", line)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    paragraph.add_run(part[2:-2]).bold = True
                else:
                    paragraph.add_run(part)

    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Calibri"
            run.font.size = Pt(10.5)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


st.title("📚 Syllabus-to-Notes Generator")
st.write(
    "Paste your university syllabus and generate structured, unit-wise study notes "
    "that you can download as a Word document."
)

with st.sidebar:
    st.header("Settings")
    detail_level = st.selectbox(
        "Notes detail",
        ["Concise", "Balanced", "Detailed"],
        index=1
    )
    audience = st.selectbox(
        "Explain for",
        ["University students", "Beginners", "Exam revision"],
        index=0
    )
    st.caption(f"Model: {MODEL_NAME}")

syllabus = st.text_area(
    "Paste your complete syllabus here",
    height=300,
    placeholder=(
        "Example:\n"
        "UNIT I - Introduction\n"
        "Meaning and scope of ...\n"
        "UNIT II - Core Concepts\n"
        "..."
    )
)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.warning(
        "Gemini API key not found. Add GEMINI_API_KEY to your .env file, "
        "then restart the app."
    )

if st.button("Generate Unit-wise Notes", type="primary", use_container_width=True):
    if not syllabus.strip():
        st.error("Please paste your syllabus first.")
    elif not api_key:
        st.error("Please configure your Gemini API key in the .env file.")
    else:
        units = split_syllabus_by_unit(syllabus)

        if not units:
            st.error(
                "I couldn't detect any unit headings. Please format headings on separate "
                "lines, for example: UNIT I, UNIT 1, MODULE II or MODULE 2."
            )
        else:
            try:
                client = genai.Client(api_key=api_key)
                all_notes = []

                st.success(f"Detected {len(units)} unit(s). Generating notes...")
                progress = st.progress(0)

                for index, unit in enumerate(units, start=1):
                    heading = unit.splitlines()[0].strip()
                    with st.expander(f"Generating: {heading}", expanded=True):
                        with st.spinner(f"Generating notes for {heading}..."):
                            notes = generate_unit_notes(
                                client, unit, detail_level, audience
                            )
                        st.markdown(notes)
                    all_notes.append((heading, notes))
                    progress.progress(index / len(units))

                combined_markdown = ""
                for heading, notes in all_notes:
                    combined_markdown += f"\n\n# {heading}\n\n{notes}\n"

                docx_file = markdown_to_docx(
                    combined_markdown,
                    "Syllabus-Based Study Notes"
                )

                st.download_button(
                    label="⬇️ Download All Notes (.docx)",
                    data=docx_file,
                    file_name="syllabus_study_notes.docx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    ),
                    use_container_width=True
                )
                st.info(
                    "Review the generated notes against your original syllabus before "
                    "using them for exam preparation."
                )

            except Exception as error:
                st.error(f"Something went wrong while generating notes: {error}")

st.divider()
st.caption("Built with Python • Streamlit • Gemini API • python-docx")
