# Study Buddy CLI App

Study Buddy is a Python command-line quiz application that uses the Google Gemini API (via the `google-genai` SDK) to generate custom 5-question multiple-choice quizzes based on your study notes or topics. It tests your knowledge, provides real-time explanations, and gives personalized study recommendations.

## Prerequisites

- Python 3.10 or higher
- A Google Gemini API Key

## Setup Instructions

### 1. Clone or Open the Directory
Make sure you are in the application directory:
```bash
cd study-buddy-agent
```

### 2. Install Dependencies
It's recommended to use a virtual environment:
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows (Command Prompt):
venv\Scripts\activate.bat
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Set the `GEMINI_API_KEY` Environment Variable
You must configure the `GEMINI_API_KEY` environment variable. Replace `your_api_key_here` with your actual Gemini API key.

#### Windows (Command Prompt)
```cmd
set GEMINI_API_KEY=your_api_key_here
```

#### Windows (PowerShell)
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

#### macOS / Linux
```bash
export GEMINI_API_KEY="your_api_key_here"
```

---

## How to Run

After setting the environment variable and activating your virtual environment, run the app.

### 1. Run Interactively (Menu Selection)
Run it without arguments to choose between typing a topic or pasting study notes:
```bash
python study_buddy.py
```

- If pasting notes, paste them and press:
  - **Windows**: `Ctrl + Z` and then `Enter`
  - **macOS/Linux**: `Ctrl + D`

### 2. Run Directly with a Topic (Quick Demo)
Skip the interactive menu by passing the `--topic` flag:
```bash
python study_buddy.py --topic "Photosynthesis"
```
```bash
python study_buddy.py --topic "Machine Learning Basics"
```

---

## Game Play Features:
- **Terminal Colors**: Highlighting correct (`✅ Correct!`) and incorrect (`❌ Incorrect`) choices in color for readability.
- **Grading & Explanations**: Answers are graded in real-time, accompanied by a clear explanation.
- **Smart Recommendations**: If you miss any questions, Gemini analyzes your performance and suggests what topic/concepts you should review next in exactly one sentence.
