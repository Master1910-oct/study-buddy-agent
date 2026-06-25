# Study Buddy — AI Quiz App

Study Buddy is an AI-powered quiz application built with Google Gemini. Enter any study topic and get a personalised 5-question multiple-choice quiz with instant grading, coached explanations, and a smart score summary. Available as both a **Streamlit web UI** and a **command-line interface**.

## Project Structure

```
study-buddy-agent/
├── agents.py          # Shared AI agents (quiz generation + grading coach)
├── app.py             # Streamlit web UI
├── study_buddy.py     # CLI entry-point
└── requirements.txt
```

### Agent Architecture

| Agent | File | Role |
|---|---|---|
| **Quiz Generator Agent** | `agents.py` | Generates 5 MCQ questions via Gemini structured output |
| **Grading Coach Agent** | `agents.py` | Grades each answer and provides a tailored coaching tip |

Both agents are defined in `agents.py` and reused by both the CLI and the web UI.

---

## Prerequisites

- Python 3.10 or higher
- A Google Gemini API Key ([get one here](https://aistudio.google.com/app/apikey))

---

## Setup

### 1. Clone / open the directory
```bash
cd study-buddy-agent
```

### 2. Create & activate a virtual environment
```bash
# Create
python -m venv venv

# Activate — Windows (Command Prompt)
venv\Scripts\activate.bat

# Activate — Windows (PowerShell)
venv\Scripts\Activate.ps1

# Activate — macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your Gemini API key

#### Windows — Command Prompt
```cmd
set GEMINI_API_KEY=your_api_key_here
```

#### Windows — PowerShell
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

#### macOS / Linux
```bash
export GEMINI_API_KEY="your_api_key_here"
```

#### Streamlit secrets (alternative for the web UI)
Create `.streamlit/secrets.toml` in the project root:
```toml
GEMINI_API_KEY = "your_api_key_here"
```

---

## Running the App

### Option A — Streamlit Web UI (recommended)
```bash
streamlit run app.py
```
Then open **http://localhost:8501** in your browser.

**UI features:**
- Clean dark-mode design with gradient colour theme
- Text input for your study topic
- One question at a time with radio-button options
- Instant colour-coded feedback (✅ green / ❌ red) after each answer
- Live coaching explanation from Gemini when you answer incorrectly
- Animated progress bar tracking your position in the quiz
- Final score summary with performance badge and personalised review recommendation
- "Try New Topic" and "Retry Same Topic" buttons

### Option B — Command-Line Interface
```bash
python study_buddy.py
```
Choose between entering a single-line topic or pasting multi-line study notes.

- If pasting notes, signal end-of-input with:
  - **Windows**: `Ctrl + Z` then `Enter`
  - **macOS / Linux**: `Ctrl + D`

---

## Features

| Feature | Web UI | CLI |
|---|:---:|:---:|
| AI-generated 5-question MCQ quiz | ✅ | ✅ |
| Input validation (empty / too long) | ✅ | ✅ |
| Retry-once on Gemini API errors | ✅ | ✅ |
| Instant grading per question | ✅ | ✅ |
| Gemini coaching tip on wrong answers | ✅ | ✅ |
| Final score + review recommendation | ✅ | ✅ |
| Colour-coded visual feedback | ✅ | — |
| Progress bar | ✅ | — |
| Retry same topic | ✅ | — |
| Paste multi-line study notes | — | ✅ |
