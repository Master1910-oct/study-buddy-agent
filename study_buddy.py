"""
study_buddy.py — CLI entry-point for Study Buddy
==================================================
This module provides the interactive command-line quiz experience.
All agent logic (quiz generation & grading) lives in agents.py so it can
be reused by the Streamlit UI in app.py.
"""

import sys

from agents import (
    Quiz,
    TOPIC_MAX_LENGTH,
    quiz_generator_agent,
    grading_coach_agent,
    get_api_key,
)

# ---------------------------------------------------------------------------
# Guard: fail fast in the CLI if the API key is missing
#
# NOTE: We call get_api_key() here (a function) instead of importing the
# GEMINI_API_KEY variable directly. agents.py only resolves the key lazily
# inside get_api_key() — the raw module-level GEMINI_API_KEY variable is
# still an empty string at import time. Importing that variable by name
# would capture its stale, empty value forever, so this check would always
# fail even when the environment variable IS set correctly.
# ---------------------------------------------------------------------------

if not get_api_key():
    print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
    print("Please set the GEMINI_API_KEY environment variable and try again.", file=sys.stderr)
    print("Example (Windows CMD): set GEMINI_API_KEY=your_api_key_here", file=sys.stderr)
    print("Example (Windows PowerShell): $env:GEMINI_API_KEY=\"your_api_key_here\"", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Orchestrator — main()
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("                    STUDY BUDDY QUIZ                    ")
    print("=" * 60)
    print("Select how you would like to provide the study material:")
    print("  1. Enter a topic (single line)")
    print("  2. Paste study notes (multi-line)")

    choice = ""
    while choice not in ["1", "2"]:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice not in ["1", "2"]:
            print("Invalid choice. Please enter 1 or 2.")

    if choice == "1":
        raw_topic = input("\nEnter the study topic (e.g. 'Photosynthesis'): ").strip()
    else:
        print("\nPaste your study notes below.")
        print(
            "Once pasted, press Ctrl+Z (Windows) or Ctrl+D (Mac/Linux) "
            "and then Enter to finish:"
        )
        try:
            raw_topic = sys.stdin.read().strip()
        except KeyboardInterrupt:
            print("\nOperation cancelled. Exiting.")
            sys.exit(0)

    # ---- Delegate to Quiz Generator Agent --------------------------------
    print("\nGenerating exactly 5 quiz questions. Please wait…")
    try:
        quiz: Quiz = quiz_generator_agent(raw_topic)
    except ValueError as ve:
        print(f"\n❌ Input error: {ve}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as re:
        print(f"\n❌ {re}", file=sys.stderr)
        sys.exit(1)

    questions = quiz.questions[:5]
    if not questions:
        print("Failed to generate questions. Gemini returned an empty list.", file=sys.stderr)
        sys.exit(1)

    # ---- Quiz loop — delegate grading to Grading Coach Agent -------------
    score = 0
    option_letters = ["A", "B", "C", "D"]

    for idx, q in enumerate(questions, 1):
        print("\n" + "=" * 60)
        print(f"QUESTION {idx} of 5:")
        print(q.question)
        print("-" * 60)

        opts = q.options
        if len(opts) < 4:
            opts = opts + [""] * (4 - len(opts))
        elif len(opts) > 4:
            opts = opts[:4]

        for letter, opt in zip(option_letters, opts):
            print(f"  {letter}) {opt}")

        user_ans = ""
        while user_ans not in option_letters:
            user_ans = input("\nYour answer (A/B/C/D): ").strip().upper()
            if user_ans not in option_letters:
                print("Invalid choice. Please select A, B, C, or D.")

        correct_ans = q.correct_option.strip().upper()

        # Delegate grading and coaching to Grading Coach Agent
        result = grading_coach_agent(
            question=q.question,
            user_answer=user_ans,
            correct_answer=correct_ans,
        )

        print(f"\n{result['feedback']}")
        if result["is_correct"]:
            score += 1
        else:
            print(f"Explanation: {q.explanation}")
            print(f"Coach says: {result['explanation']}")

        input("\nPress Enter to continue…")

    # ---- Final results ---------------------------------------------------
    print("\n" + "=" * 60)
    print("                      QUIZ COMPLETE                     ")
    print("=" * 60)
    print(f"Your final score: {score}/5")

    if score == 5:
        print("Review Recommendation: Outstanding performance! You have fully mastered this material.")
    else:
        print("Review Recommendation: Focus on reviewing the questions you got wrong to reinforce the core concepts.")


if __name__ == "__main__":
    main()
