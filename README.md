# Syllabus-to-Notes Generator

A GenAI mini project that converts a university syllabus into organised, unit-wise study notes and exports them as a Word document.

## Tech stack
- Python
- Streamlit
- Google Gemini API (`google-genai`)
- Regex for unit detection
- `python-docx` for Word export
- `python-dotenv` for API-key configuration

## Setup (Windows)

1. Extract the ZIP and open the project folder in VS Code.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt:

   ```cmd
   venv\Scripts\activate.bat
   ```

3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Copy `.env.example` and rename the copy to `.env`.
5. Get a Gemini API key from Google AI Studio and paste it into `.env`.
6. Run the app:

   ```bash
   streamlit run app.py
   ```

## Input format

Put each unit heading on a separate line. Supported examples:

- `UNIT I - Introduction`
- `UNIT 1: Introduction`
- `MODULE II - Core Concepts`
- `MODULE 2: Applications`

The application detects the headings, splits the syllabus into units, makes one Gemini request per unit, displays the notes, and creates a downloadable `.docx` file.

## Important
- Never upload `.env` or expose your API key on GitHub.
- Generated notes should be checked against the original syllabus.
- API access, model availability and quotas depend on your Google AI Studio account.
