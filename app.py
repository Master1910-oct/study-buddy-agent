"""
app.py — Streamlit Web UI for Study Buddy
==========================================
A polished, single-page Streamlit application that guides students through
a 5-question AI-generated multiple-choice quiz, gives instant colour-coded
feedback after each answer, and displays a styled summary at the end.

Agent logic is entirely delegated to agents.py (quiz_generator_agent &
grading_coach_agent), keeping UI and business logic cleanly separated.
"""

import re as _re
import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be the very first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Study Buddy — AI Quiz",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Import agents (may raise ImportWarning if google-genai is missing)
# ---------------------------------------------------------------------------

from agents import (  # noqa: E402  (import after set_page_config is intentional)
    get_api_key,
    quiz_generator_agent,
    grading_coach_agent,
)

# ---------------------------------------------------------------------------
# Global CSS — design tokens, layout, components
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* ---- Google Font ---- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ---- Root tokens ---- */
    :root {
        --clr-bg:        #0f1117;
        --clr-surface:   #1a1d2e;
        --clr-surface2:  #22253a;
        --clr-border:    #2e3150;
        --clr-primary:   #6c63ff;
        --clr-primary-h: #8b84ff;
        --clr-accent:    #00d4aa;
        --clr-success:   #22c55e;
        --clr-error:     #ef4444;
        --clr-warn:      #f59e0b;
        --clr-text:      #e8eaf6;
        --clr-muted:     #8b92b8;
        --radius:        14px;
        --shadow:        0 8px 32px rgba(0,0,0,0.45);
    }

    /* ---- Base ---- */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
        background-color: var(--clr-bg) !important;
        color: var(--clr-text) !important;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    .block-container { max-width: 780px; padding: 2rem 1.5rem 4rem; }

    /* ---- Hero title ---- */
    .hero {
        text-align: center;
        padding: 2.5rem 0 1.5rem;
    }
    .hero-icon { font-size: 3.2rem; line-height: 1; }
    .hero h1 {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6c63ff 0%, #00d4aa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0.3rem 0 0.5rem;
        letter-spacing: -0.5px;
    }
    .hero p {
        color: var(--clr-muted);
        font-size: 1.05rem;
        margin: 0;
    }

    /* ---- Card ---- */
    .card {
        background: var(--clr-surface);
        border: 1px solid var(--clr-border);
        border-radius: var(--radius);
        padding: 1.8rem;
        margin-bottom: 1.2rem;
        box-shadow: var(--shadow);
    }

    /* ---- Progress bar custom ---- */
    .progress-wrap {
        background: var(--clr-surface2);
        border-radius: 999px;
        height: 8px;
        overflow: hidden;
        margin-bottom: 0.4rem;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #6c63ff, #00d4aa);
        border-radius: 999px;
        transition: width 0.4s ease;
    }
    .progress-label {
        font-size: 0.78rem;
        color: var(--clr-muted);
        text-align: right;
        margin-bottom: 1.2rem;
    }

    /* ---- Question heading ---- */
    .q-number {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--clr-primary);
        margin-bottom: 0.5rem;
    }
    .q-text {
        font-size: 1.15rem;
        font-weight: 600;
        line-height: 1.55;
        color: var(--clr-text);
        margin-bottom: 1.3rem;
    }

    /* ---- Radio options ---- */
    div[data-testid="stRadio"] > label {
        display: none !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 0.55rem;
        display: flex;
        flex-direction: column;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background: var(--clr-surface2) !important;
        border: 1.5px solid var(--clr-border) !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
        cursor: pointer;
        transition: border-color 0.2s, background 0.2s;
        font-size: 0.97rem !important;
        color: var(--clr-text) !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        border-color: var(--clr-primary) !important;
        background: #1e2040 !important;
    }
    div[data-testid="stRadio"] label[aria-checked="true"][data-baseweb="radio"] {
        border-color: var(--clr-primary) !important;
        background: rgba(108,99,255,0.12) !important;
    }
    /* Ensure radio option text is always clearly visible — covers all
       Streamlit internal span/p variants that render the label markdown. */
    div[data-testid="stRadio"] span[data-testid="stMarkdownContainer"] p,
    div[data-testid="stRadio"] span[data-testid="stMarkdownContainer"],
    div[data-testid="stRadio"] label[data-baseweb="radio"] span,
    div[data-testid="stRadio"] label[data-baseweb="radio"] p,
    div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p {
        font-size: 0.97rem !important;
        color: var(--clr-text) !important;
        margin: 0 !important;
    }

    /* ---- Feedback boxes ---- */
    .feedback-correct {
        background: rgba(34,197,94,0.12);
        border: 1.5px solid var(--clr-success);
        border-radius: var(--radius);
        padding: 1.1rem 1.3rem;
        margin-top: 1rem;
    }
    .feedback-correct .fb-title { color: var(--clr-success); font-size: 1.05rem; font-weight: 700; }
    .feedback-wrong {
        background: rgba(239,68,68,0.10);
        border: 1.5px solid var(--clr-error);
        border-radius: var(--radius);
        padding: 1.1rem 1.3rem;
        margin-top: 1rem;
    }
    .feedback-wrong .fb-title { color: var(--clr-error); font-size: 1.05rem; font-weight: 700; }
    .fb-explanation {
        color: var(--clr-muted);
        font-size: 0.91rem;
        margin-top: 0.55rem;
        line-height: 1.6;
    }
    .fb-coach {
        color: var(--clr-accent);
        font-size: 0.88rem;
        margin-top: 0.45rem;
        font-style: italic;
        line-height: 1.55;
    }

    /* ---- Buttons ---- */
    div[data-testid="stButton"] > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.97rem !important;
        transition: transform 0.15s, box-shadow 0.15s !important;
        border: none !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #6c63ff, #00d4aa) !important;
        color: #fff !important;
        padding: 0.65rem 2rem !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(108,99,255,0.45) !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"] {
        background: var(--clr-surface2) !important;
        color: var(--clr-text) !important;
        border: 1.5px solid var(--clr-border) !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        border-color: var(--clr-primary) !important;
        transform: translateY(-1px) !important;
    }

    /* ---- Text input ---- */
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input {
        background: var(--clr-surface2) !important;
        border: 1.5px solid var(--clr-border) !important;
        border-radius: 10px !important;
        color: var(--clr-text) !important;
        font-family: 'Inter', sans-serif !important;
    }
    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stTextInput"] input:focus {
        border-color: var(--clr-primary) !important;
        box-shadow: 0 0 0 3px rgba(108,99,255,0.2) !important;
    }
    div[data-testid="stTextArea"] label,
    div[data-testid="stTextInput"] label {
        color: var(--clr-muted) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }

    /* ---- Score summary ---- */
    .summary-card {
        background: linear-gradient(135deg, #1a1d2e 0%, #22253a 100%);
        border: 2px solid var(--clr-primary);
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        box-shadow: 0 0 60px rgba(108,99,255,0.2);
        margin-top: 1rem;
    }
    .summary-score {
        font-size: 4.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6c63ff, #00d4aa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.1;
    }
    .summary-label {
        color: var(--clr-muted);
        font-size: 1rem;
        margin-top: 0.3rem;
    }
    .summary-badge {
        display: inline-block;
        margin-top: 1.2rem;
        padding: 0.45rem 1.2rem;
        border-radius: 999px;
        font-size: 0.88rem;
        font-weight: 600;
    }
    .badge-perfect { background: rgba(34,197,94,0.2); color: var(--clr-success); border: 1px solid var(--clr-success); }
    .badge-good    { background: rgba(108,99,255,0.2); color: var(--clr-primary-h); border: 1px solid var(--clr-primary); }
    .badge-keep-at { background: rgba(245,158,11,0.15); color: var(--clr-warn); border: 1px solid var(--clr-warn); }
    .summary-rec {
        margin-top: 1.4rem;
        background: var(--clr-surface);
        border: 1px solid var(--clr-border);
        border-radius: 12px;
        padding: 1rem 1.3rem;
        font-size: 0.93rem;
        color: var(--clr-text);
        line-height: 1.65;
        text-align: left;
    }
    .rec-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--clr-accent);
        margin-bottom: 0.4rem;
    }

    /* ---- Code blocks (from st.markdown code fences) ---- */
    /* Ensure pre/code inside the question markdown renders as a proper
       monospace block with visible background, line breaks, and scrolling. */
    [data-testid="stMarkdownContainer"] pre {
        background: #0d1117 !important;
        border: 1px solid var(--clr-border) !important;
        border-radius: 8px !important;
        padding: 1rem 1.2rem !important;
        overflow-x: auto !important;
        margin: 0.75rem 0 !important;
        white-space: pre !important;
    }
    [data-testid="stMarkdownContainer"] pre code {
        font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace !important;
        font-size: 0.88rem !important;
        line-height: 1.6 !important;
        color: #e6edf3 !important;
        white-space: pre !important;
        background: transparent !important;
        padding: 0 !important;
    }
    /* Inline code */
    [data-testid="stMarkdownContainer"] code:not(pre code) {
        font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace !important;
        font-size: 0.87em !important;
        background: rgba(110,118,129,0.2) !important;
        border-radius: 4px !important;
        padding: 0.15em 0.4em !important;
        color: var(--clr-accent) !important;
    }

    /* ---- Misc ---- */
    hr { border-color: var(--clr-border) !important; margin: 1.4rem 0 !important; }
    .stSpinner > div { border-top-color: var(--clr-primary) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

DEFAULTS: dict = {
    "stage": "input",          # input | quiz | result
    "quiz": None,              # Quiz object
    "q_index": 0,              # current question index (0–4)
    "score": 0,
    "answers": [],             # list of result dicts per question
    "submitted": False,        # has the current question been submitted?
    "last_result": None,       # grading result dict for the current question
    "topic": "",
}

for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

OPTION_LETTERS = ["A", "B", "C", "D"]


def reset_quiz() -> None:
    """Reset all quiz state back to the input stage."""
    for key, default in DEFAULTS.items():
        st.session_state[key] = default
    if "topic_input_widget" in st.session_state:
        st.session_state["topic_input_widget"] = ""


_OPTION_PREFIX_RE = _re.compile(
    r"^[A-Da-d][\s)\.]\s*",  # matches "A) ", "A. ", "A ", "a) " etc.
)


def _strip_option_prefix(text: str) -> str:
    """Remove any leading letter-prefix that Gemini may have baked into the
    option text (e.g. 'A) foo' → 'foo') so that _radio_label's own prefix
    is never duplicated."""
    return _OPTION_PREFIX_RE.sub("", text.strip())


def _radio_label(letter: str, text: str) -> str:
    return f"**{letter})** {_strip_option_prefix(text)}"


def _score_badge(score: int) -> str:
    if score == 5:
        return '<span class="summary-badge badge-perfect">🏆 Perfect Score!</span>'
    if score >= 3:
        return '<span class="summary-badge badge-good">⭐ Great Work</span>'
    return '<span class="summary-badge badge-keep-at">💪 Keep Practising</span>'


def _review_text(score: int) -> str:
    if score == 5:
        return "Outstanding performance! You have fully mastered this material. Consider challenging yourself with a harder topic next."
    if score >= 3:
        return "Solid effort! Review the questions you missed and pay extra attention to the coach's hints — you're very close to mastering this topic."
    return "Keep at it! Focus on the explanations for the questions you got wrong and revisit the core concepts before trying again."


# ---------------------------------------------------------------------------
# UI: API-key guard
# ---------------------------------------------------------------------------

if not get_api_key():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-icon">⚠️</div>
            <h1>API Key Missing</h1>
            <p>Set <code>GEMINI_API_KEY</code> in your environment or Streamlit secrets and restart.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ---------------------------------------------------------------------------
# Hero header (always visible)
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="hero-icon">🎓</div>
        <h1>Study Buddy</h1>
        <p>AI-powered quizzes · Instant coaching · Master any topic</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ===========================================================================
# STAGE: input
# ===========================================================================

if st.session_state.stage == "input":
    topic_input = st.text_input(
        "Study topic",
        placeholder="e.g. Photosynthesis, World War II, Python decorators…",
        max_chars=500,
        key="topic_input_widget",
        label_visibility="visible",
    )

    st.markdown(
        "<p style='color:#8b92b8; font-size:0.8rem; margin-top:-0.6rem;'>"
        "Enter a topic or short study notes (max 500 characters)</p>",
        unsafe_allow_html=True,
    )

    col_btn, col_spacer = st.columns([1, 2])
    with col_btn:
        generate_clicked = st.button(
            "✨ Generate Quiz",
            type="primary",
            use_container_width=True,
            key="btn_generate",
        )


    if generate_clicked:
        topic = topic_input.strip()
        if not topic:
            st.error("⚠️ Please enter a topic before generating the quiz.")
        elif len(topic) > 500:
            st.error(f"⚠️ Topic is too long ({len(topic)} chars). Keep it under 500.")
        else:
            with st.spinner("🤖 Generating your personalised quiz — hang tight…"):
                try:
                    quiz = quiz_generator_agent(topic)
                    st.session_state.quiz = quiz
                    st.session_state.topic = topic
                    st.session_state.stage = "quiz"
                    st.session_state.q_index = 0
                    st.session_state.score = 0
                    st.session_state.answers = []
                    st.session_state.submitted = False
                    st.session_state.last_result = None
                    st.rerun()
                except ValueError as ve:
                    st.error(f"❌ Input error: {ve}")
                except RuntimeError as re:
                    st.error(f"❌ {re}")

# ===========================================================================
# STAGE: quiz
# ===========================================================================

elif st.session_state.stage == "quiz":
    quiz = st.session_state.quiz
    q_index = st.session_state.q_index
    questions = quiz.questions[:5]
    q = questions[q_index]

    total = len(questions)
    pct = int((q_index / total) * 100)

    # Progress bar
    st.markdown(
        f"""
        <div class="progress-wrap">
            <div class="progress-fill" style="width:{pct}%"></div>
        </div>
        <div class="progress-label">Question {q_index + 1} of {total}</div>
        """,
        unsafe_allow_html=True,
    )

    # Normalise options to exactly 4
    opts = q.options
    if len(opts) < 4:
        opts = opts + ["(no option)"] * (4 - len(opts))
    elif len(opts) > 4:
        opts = opts[:4]

    # Question number label
    st.markdown(f'<div class="q-number">Question {q_index + 1}</div>', unsafe_allow_html=True)
    # Use st.markdown so that triple-backtick code fences in the question text
    # are rendered as proper syntax-highlighted, monospace code blocks.
    st.markdown(q.question)

    radio_options = [_radio_label(letter, text) for letter, text in zip(OPTION_LETTERS, opts)]

    # Disable radio once the answer is submitted
    selected = st.radio(
        "Choose your answer",
        options=radio_options,
        key=f"radio_q{q_index}",
        disabled=st.session_state.submitted,
        label_visibility="collapsed",
    )


    # ---- Submit button --------------------------------------------------
    if not st.session_state.submitted:
        if st.button("📝 Submit Answer", type="primary", key="btn_submit"):
            # Derive letter from selected radio label (first char)
            user_letter = selected[2]  # "**A)**  …" → 'A'
            correct_ans = q.correct_option.strip().upper()

            with st.spinner("🤔 Coach is reviewing your answer…"):
                result = grading_coach_agent(
                    question=q.question,
                    user_answer=user_letter,
                    correct_answer=correct_ans,
                )

            st.session_state.submitted = True
            st.session_state.last_result = result
            if result["is_correct"]:
                st.session_state.score += 1
            st.rerun()

    # ---- Show feedback after submission ---------------------------------
    if st.session_state.submitted:
        result = st.session_state.last_result

        if result["is_correct"]:
            st.markdown(
                f"""
                <div class="feedback-correct">
                    <div class="fb-title">{result['feedback']}</div>
                    <div class="fb-explanation">{q.explanation}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="feedback-wrong">
                    <div class="fb-title">{result['feedback']}</div>
                    <div class="fb-explanation"><strong>Explanation:</strong> {q.explanation}</div>
                    <div class="fb-coach">💬 Coach says: {result['explanation']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Running score chip
        current_score = st.session_state.score
        answered = q_index + 1
        st.markdown(
            f"<p style='color:#8b92b8; font-size:0.85rem; margin-top:0.8rem;'>"
            f"Score so far: <strong style='color:#e8eaf6'>{current_score}/{answered}</strong></p>",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Next / Finish button
        is_last = q_index + 1 >= total
        btn_label = "🏁 See My Results" if is_last else "➡️ Next Question"

        if st.button(btn_label, type="primary", key="btn_next"):
            if is_last:
                st.session_state.stage = "result"
            else:
                st.session_state.q_index += 1
                st.session_state.submitted = False
                st.session_state.last_result = None
            st.rerun()

# ===========================================================================
# STAGE: result
# ===========================================================================

elif st.session_state.stage == "result":
    score = st.session_state.score
    total = 5
    pct_correct = int((score / total) * 100)

    # Completed progress bar
    st.markdown(
        """
        <div class="progress-wrap">
            <div class="progress-fill" style="width:100%"></div>
        </div>
        <div class="progress-label">Quiz Complete ✓</div>
        """,
        unsafe_allow_html=True,
    )

    # Summary card
    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-score">{score}/{total}</div>
            <div class="summary-label">You answered {pct_correct}% of questions correctly</div>
            {_score_badge(score)}
            <div class="summary-rec">
                <div class="rec-title">📚 Review Recommendation</div>
                {_review_text(score)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔁 Try a New Topic", type="primary", use_container_width=True, key="btn_new"):
            reset_quiz()
            st.rerun()
    with col_b:
        if st.button(
            "🔄 Retry Same Topic",
            type="secondary",
            use_container_width=True,
            key="btn_retry",
        ):
            saved_topic = st.session_state.topic
            reset_quiz()
            # Pre-fill the topic so the user can hit generate immediately
            st.session_state.topic = saved_topic
            st.session_state["topic_input_widget"] = saved_topic
            st.rerun()
