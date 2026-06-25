"""
agents.py — Shared Study Buddy Agent Module
============================================
This module owns the Gemini client, Pydantic schemas, and the two core
agent functions.  Both the CLI (study_buddy.py) and the Streamlit UI
(app.py) import from here so the logic lives in exactly one place.
"""

import os
import sys
import warnings
from typing import List

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# SDK import
# ---------------------------------------------------------------------------

try:
    from google import genai
    from google.genai import types
except ImportError:
    warnings.warn(
        "The 'google-genai' package is not installed. "
        "Run: pip install -r requirements.txt",
        ImportWarning,
        stacklevel=2,
    )
    raise

# ---------------------------------------------------------------------------
# Gemini client — initialised once at module load
# ---------------------------------------------------------------------------


def _resolve_api_key() -> str:
    """
    Resolve the Gemini API key from (in priority order):
      1. Streamlit secrets (st.secrets["GEMINI_API_KEY"]) — checked first so
         that .streamlit/secrets.toml always wins when running under Streamlit.
      2. GEMINI_API_KEY environment variable — fallback for the CLI and any
         environment where Streamlit secrets are not available.

    NOTE: This function is called lazily from get_api_key() / get_client()
    rather than at module import time, so that Streamlit's secrets context is
    fully initialised before we attempt to read it.
    """
    # 1. Streamlit secrets — only available when running inside Streamlit
    try:
        import streamlit as st  # noqa: PLC0415
        key = st.secrets.get("GEMINI_API_KEY", "").strip()
        if key:
            return key
    except Exception:
        pass

    # 2. Environment variable — used by the CLI and CI/CD environments
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key

    return ""


# ---------------------------------------------------------------------------
# Lazy accessors — call these from within a running Streamlit page or the CLI
# so that secrets/env are resolved at call-time, not at import-time.
# ---------------------------------------------------------------------------

_client = None  # module-level cache; populated on first get_client() call


def get_api_key() -> str:
    """Return the resolved API key (cached after first call)."""
    global GEMINI_API_KEY  # noqa: PLW0603
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = _resolve_api_key()
    return GEMINI_API_KEY


def get_client():
    """Return (and lazily initialise) the shared Gemini client."""
    global _client  # noqa: PLW0603
    if _client is not None:
        return _client
    key = get_api_key()
    if not key:
        return None
    try:
        _client = genai.Client(api_key=key)
    except Exception as _e:
        warnings.warn(f"Failed to initialise Gemini client: {_e}", RuntimeWarning, stacklevel=2)
        _client = None
    return _client


# Public constant — empty at import time; populated on first get_api_key() call.
GEMINI_API_KEY: str = ""

# ---------------------------------------------------------------------------
# Input validation constants
# ---------------------------------------------------------------------------

TOPIC_MIN_LENGTH: int = 1     # must not be empty after strip
TOPIC_MAX_LENGTH: int = 500   # characters — prevents runaway prompts

# ---------------------------------------------------------------------------
# Pydantic schemas for structured output
# ---------------------------------------------------------------------------


class QuizQuestion(BaseModel):
    """A single multiple-choice quiz question with 4 options."""

    question: str = Field(
        description="The multiple-choice question testing understanding of the provided notes or topic."
    )
    options: List[str] = Field(description="Exactly 4 distinct multiple-choice options.")
    correct_option: str = Field(
        description="The correct option letter, which must be one of: A, B, C, or D."
    )
    explanation: str = Field(
        description="A short explanation of why the correct option is right."
    )


class Quiz(BaseModel):
    """A structured quiz containing exactly 5 MCQ questions."""

    questions: List[QuizQuestion] = Field(description="Exactly 5 multiple-choice questions.")


# ---------------------------------------------------------------------------
# Agent 1 — Quiz Generator Agent
# ---------------------------------------------------------------------------


def quiz_generator_agent(topic: str) -> Quiz:
    """
    Agent: Quiz Generator Agent
    Role: An expert tutor that receives a study topic or notes and autonomously
          crafts a structured, 5-question multiple-choice quiz.  It is solely
          responsible for question composition and correct-answer labelling; it
          does NOT grade or explain student performance.

    Skill: Generate exactly 5 high-quality MCQ questions with 4 options each,
           a clearly identified correct option (A/B/C/D), and a brief
           explanation — returned as a validated Pydantic ``Quiz`` object.

    Args:
        topic (str): A non-empty string (max 500 chars) describing the study
                     topic or pasted study notes to quiz the student on.

    Returns:
        Quiz: A Pydantic model containing exactly 5 QuizQuestion objects.

    Raises:
        ValueError:   If the topic fails input validation (empty or too long).
        RuntimeError: If the Gemini client is not initialised, or if the API
                      call / JSON parsing fails after one automatic retry.
    """
    # ---- Pre-flight check -----------------------------------------------
    client = get_client()
    if client is None:
        raise RuntimeError(
            "Gemini client is not initialised. "
            "Please set the GEMINI_API_KEY environment variable (or Streamlit secret) and restart."
        )

    # ---- Input validation -----------------------------------------------
    if not isinstance(topic, str):
        raise ValueError("Topic must be a string.")

    topic = topic.strip()

    if len(topic) < TOPIC_MIN_LENGTH:
        raise ValueError(
            "Topic cannot be empty. Please provide a study topic or notes."
        )

    if len(topic) > TOPIC_MAX_LENGTH:
        raise ValueError(
            f"Topic is too long ({len(topic)} characters). "
            f"Please keep it under {TOPIC_MAX_LENGTH} characters."
        )

    # ---- Build prompt ---------------------------------------------------
    prompt = (
        "You are an expert tutor. Based on the provided topic or study notes, "
        "generate a high-quality quiz with exactly 5 multiple choice questions. "
        "Each question must have exactly 4 options. Specify the correct option as "
        "A, B, C, or D. Provide a short explanation for the correct answer.\n\n"
        "IMPORTANT FORMATTING RULE: If any question includes a code snippet, "
        "you MUST wrap it in a triple-backtick markdown code fence with the "
        "language name (e.g. ```java, ```python, ```javascript). "
        "Always add a blank line before the opening fence and after the closing "
        "fence so the block renders correctly. Never write code inline without fences.\n\n"
        f"Topic: {topic}"
    )

    # ---- Call Gemini with one automatic retry on failure ----------------
    def _call_api() -> str:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Quiz,
                temperature=0.2,
            ),
        )
        return response.text

    last_error: Exception | None = None
    for attempt in range(1, 3):          # attempt 1, then retry (attempt 2)
        try:
            raw_json = _call_api()
            quiz = Quiz.model_validate_json(raw_json)
            return quiz
        except Exception as exc:
            last_error = exc
            if attempt == 1:
                print(
                    "\n⚠️  Quiz generation encountered an issue — retrying once…",
                    file=sys.stderr,
                )

    # Both attempts failed — raise a friendly RuntimeError
    raise RuntimeError(
        "Sorry, we couldn't generate the quiz after two attempts. "
        "Please check your network connection and API key, then try again.\n"
        f"(Technical detail: {last_error})"
    )


# ---------------------------------------------------------------------------
# Agent 2 — Grading Coach Agent
# ---------------------------------------------------------------------------


def grading_coach_agent(
    question: str,
    user_answer: str,
    correct_answer: str,
) -> dict:
    """
    Agent: Grading Coach Agent
    Role: A supportive academic coach that evaluates a single quiz response,
          decides whether it is correct, and delivers targeted, encouraging
          feedback.  It is solely responsible for assessment and explanation;
          it does NOT generate questions or track overall scores.

    Skill: Compare a student's selected option against the correct option for
           a given question, then return a structured result dict containing
           ``is_correct`` (bool), ``feedback`` (str with emoji prefix), and
           ``explanation`` (str) — either a congratulatory note or a
           Gemini-generated coaching tip for the missed concept.

    Args:
        question (str):       The text of the quiz question that was asked.
        user_answer (str):    The option letter the student chose (A/B/C/D).
        correct_answer (str): The option letter that is correct (A/B/C/D).

    Returns:
        dict with keys:
            is_correct  (bool) — True if the student answered correctly.
            feedback    (str)  — One-line result message with ✅ or ❌ emoji.
            explanation (str)  — Coaching explanation for the student.

    Raises:
        ValueError: If any argument is empty or whitespace-only.
    """
    # ---- Input validation -----------------------------------------------
    if not question or not question.strip():
        raise ValueError("question must not be empty.")
    if not user_answer or not user_answer.strip():
        raise ValueError("user_answer must not be empty.")
    if not correct_answer or not correct_answer.strip():
        raise ValueError("correct_answer must not be empty.")

    user_answer = user_answer.strip().upper()
    correct_answer = correct_answer.strip().upper()

    is_correct = user_answer == correct_answer

    if is_correct:
        return {
            "is_correct": True,
            "feedback": "✅ Correct!",
            "explanation": "Great job — you selected the right answer. Keep it up!",
        }

    # ---- Wrong answer: ask Gemini for a tailored coaching explanation ----
    coaching_prompt = (
        "You are a supportive academic coach. A student answered a quiz question "
        "incorrectly. Provide ONE short, encouraging sentence explaining why the "
        "correct answer is right and what concept they should review.\n\n"
        f"Question: {question}\n"
        f"Student's answer: {user_answer}\n"
        f"Correct answer: {correct_answer}"
    )

    # Default explanation used if both API attempts fail
    explanation_text = (
        f"The correct answer was {correct_answer}. "
        "Review the related concept to reinforce your understanding."
    )

    client = get_client()
    if client is not None:
        last_error: Exception | None = None
        for attempt in range(1, 3):          # attempt 1, then retry (attempt 2)
            try:
                rec_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=coaching_prompt,
                    config=types.GenerateContentConfig(temperature=0.7),
                )
                explanation_text = rec_response.text.strip()
                break
            except Exception as exc:
                last_error = exc
                if attempt == 1:
                    print(
                        "\n⚠️  Coaching explanation encountered an issue — retrying once…",
                        file=sys.stderr,
                    )
        else:
            print(
                f"\n⚠️  Could not fetch a detailed explanation ({last_error}). "
                "Using a generic message.",
                file=sys.stderr,
            )

    return {
        "is_correct": False,
        "feedback": f"❌ Incorrect. The correct answer was {correct_answer}.",
        "explanation": explanation_text,
    }
