import os
import sys
from typing import List
from pydantic import BaseModel, Field
# Ensure the new google-genai SDK is imported correctly
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: The 'google-genai' package is not installed.", file=sys.stderr)
    print("Please run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)
# Check for GEMINI_API_KEY environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
    print("Please set the GEMINI_API_KEY environment variable and try again.", file=sys.stderr)
    print("Example (Windows CMD): set GEMINI_API_KEY=your_api_key_here", file=sys.stderr)
    print("Example (Windows PowerShell): $env:GEMINI_API_KEY=\"your_api_key_here\"", file=sys.stderr)
    sys.exit(1)
# Define schemas for structured JSON output
class QuizQuestion(BaseModel):
    question: str = Field(description="The multiple-choice question testing understanding of the provided notes or topic.")
    options: List[str] = Field(description="Exactly 4 distinct multiple-choice options.")
    correct_option: str = Field(description="The correct option letter, which must be one of: A, B, C, or D.")
    explanation: str = Field(description="A short explanation of why the correct option is right.")
class Quiz(BaseModel):
    questions: List[QuizQuestion] = Field(description="Exactly 5 multiple-choice questions.")
def main():
    # Initialize the Gemini Client with the API key from the environment variable
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Error initializing Gemini client: {e}", file=sys.stderr)
        sys.exit(1)
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
        topic = input("\nEnter the study topic (e.g. 'Photosynthesis'): ").strip()
        if not topic:
            print("No topic provided. Exiting.")
            sys.exit(0)
        prompt_input = f"Topic: {topic}"
    else:
        print("\nPaste your study notes below.")
        print("Once pasted, press Ctrl+Z (Windows) or Ctrl+D (Mac/Linux) and then Enter to finish:")
        try:
            notes = sys.stdin.read().strip()
        except KeyboardInterrupt:
            print("\nOperation cancelled. Exiting.")
            sys.exit(0)
        
        if not notes:
            print("No notes provided. Exiting.")
            sys.exit(0)
        prompt_input = f"Study Notes:\n{notes}"
    print("\nGenerating exactly 5 quiz questions. Please wait...")
    # Build prompt
    prompt = (
        "You are an expert tutor. Based on the provided topic or study notes, generate a high-quality quiz with exactly 5 multiple choice questions. "
        "Each question must have exactly 4 options. Specify the correct option as A, B, C, or D. "
        "Provide a short explanation for the correct answer.\n\n"
        f"{prompt_input}"
    )
    try:
        # Call Gemini 2.5 Flash with structured output schema
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Quiz,
                temperature=0.2,
            ),
        )
        
        # Parse the structured JSON response
        quiz = Quiz.model_validate_json(response.text)
    except Exception as e:
        print(f"\nError generating quiz from Gemini API: {e}", file=sys.stderr)
        print("Please check your network connection and API key permissions.", file=sys.stderr)
        sys.exit(1)
    # Ensure we have questions to display
    questions = quiz.questions[:5]  # Cap/slice to exactly 5
    if not questions:
        print("Failed to generate questions. Gemini returned an empty list.", file=sys.stderr)
        sys.exit(1)
    score = 0
    wrong_questions = []
    option_letters = ['A', 'B', 'C', 'D']
    # Present questions one at a time
    for idx, q in enumerate(questions, 1):
        print("\n" + "=" * 60)
        print(f"QUESTION {idx} of 5:")
        print(q.question)
        print("-" * 60)
        
        # Format the 4 options
        opts = q.options
        if len(opts) < 4:
            opts = opts + [""] * (4 - len(opts))
        elif len(opts) > 4:
            opts = opts[:4]
        for letter, opt in zip(option_letters, opts):
            print(f"  {letter}) {opt}")
            
        # Get user response and validate
        user_ans = ""
        while user_ans not in option_letters:
            user_ans = input("\nYour answer (A/B/C/D): ").strip().upper()
            if user_ans not in option_letters:
                print("Invalid choice. Please select A, B, C, or D.")
        # Check correctness
        correct_ans = q.correct_option.strip().upper()
        if user_ans == correct_ans:
            print("\n✅ Correct!")
            score += 1
        else:
            print(f"\n❌ Incorrect. The correct answer was {correct_ans}.")
            wrong_questions.append(q)
        print(f"Explanation: {q.explanation}")
        input("\nPress Enter to continue...")
    # Final score printing
    print("\n" + "=" * 60)
    print("                          QUIZ COMPLETE                 ")
    print("=" * 60)
    print(f"Your final score: {score}/5")
    # Generate review recommendations
    if score == 5:
        print("Review Recommendation: Outstanding performance! You have fully mastered this material.")
    else:
        print("Analyzing your performance for review recommendations...")
        try:
            missed_details = ""
            for i, q in enumerate(wrong_questions, 1):
                missed_details += f"Question {i}: {q.question}\nCorrect Answer: {q.correct_option}\nExplanation: {q.explanation}\n\n"
            review_prompt = (
                "Based on the following multiple-choice questions that a student answered incorrectly in a quiz, "
                "provide exactly ONE sentence of advice on what specific sub-topics or concepts they should review. "
                "Make it highly tailored to the topics in these questions and keep it constructive.\n\n"
                f"Incorrectly Answered Questions:\n{missed_details}"
            )
            
            # Simple unstructured content generation for the advice
            rec_response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=review_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                )
            )
            advice = rec_response.text.strip()
            print(f"Review Recommendation: {advice}")
        except Exception:
            # Fallback advice if the API call fails or times out
            print("Review Recommendation: Focus on reviewing the questions you got wrong to reinforce the core concepts.")
if __name__ == "__main__":
    main()
