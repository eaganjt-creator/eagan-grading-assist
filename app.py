import os
import streamlit as st
from google import genai

# Streamlit Page Setup
st.set_page_config(
    page_title="Prof. Eagan's Grading Assist Tool | Daniels School of Business",
    page_icon="🚂",
    layout="wide"
)

# Purdue Old Gold & Black Styling
purdue_css = """
<style>
    :root {
        --purdue-gold: #CEB888;
        --purdue-dark-gold: #9D8249;
        --purdue-black: #000000;
        --purdue-gray: #373A36;
    }
    
    .brand-banner {
        background-color: #000000;
        border-bottom: 4px solid #CEB888;
        padding: 16px 24px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: white;
    }
    .brand-banner h1 {
        color: #CEB888 !important;
        margin: 0;
        font-size: 1.85rem;
    }
    .brand-banner p {
        color: #E0E0E0;
        margin: 4px 0 0 0;
        font-size: 0.95rem;
    }

    div.stButton > button:first-child {
        background-color: #CEB888 !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border: 2px solid #9D8249 !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:first-child:hover {
        background-color: #000000 !important;
        color: #CEB888 !important;
        border-color: #CEB888 !important;
    }

    .stTextArea textarea:focus {
        border-color: #CEB888 !important;
        box-shadow: 0 0 0 1px #CEB888 !important;
    }
</style>
"""
st.markdown(purdue_css, unsafe_allow_html=True)

# Daniels School of Business Banner
st.markdown(
    """
    <div class="brand-banner">
        <h1>🚂 Prof. Eagan's Grading Assist Tool</h1>
        <p>Daniels School of Business</p>
    </div>
    """,
    unsafe_allow_html=True
)

# API Key Retrieval
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if not api_key:
    st.info("Please set GEMINI_API_KEY in Streamlit Secrets or sidebar to begin.", icon="🔑")
    st.stop()

client = genai.Client(api_key=api_key)

# Top Bar: Point Scale Configuration
top_col1, top_col2 = st.columns([1, 3])
with top_col1:
    total_points = st.number_input(
        "Question Total Points:",
        min_value=1,
        max_value=100,
        value=20,
        step=1
    )

# App UI: Input Fields
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Question Prompt")
    question_prompt = st.text_area(
        "Paste McGraw-Hill Connect Question:",
        height=140,
        placeholder="Paste student's algorithmic problem statement..."
    )

    st.subheader("2. Connect Master Solution")
    connect_solution = st.text_area(
        "Paste Connect Synthesized Solution:",
        height=180,
        placeholder="Paste Connect's generated answer and calculations..."
    )

with col2:
    st.subheader("3. Student Submission")
    student_submission = st.text_area(
        "Paste Student Answer (Anonymized - No Names/IDs):",
        height=400,
        placeholder="Paste student response here..."
    )

evaluate_btn = st.button("Evaluate Submission", use_container_width=True)

if evaluate_btn:
    if not (question_prompt.strip() and connect_solution.strip() and student_submission.strip()):
        st.warning("Please paste all three fields before running evaluation.", icon="⚠️")
    else:
        with st.spinner("Analyzing against Connect solution and Prof. Eagan's standards..."):
            prompt = f"""
You are an expert tax accounting teaching assistant evaluating student exam submissions for Prof. Eagan at Purdue University's Daniels School of Business.

TOTAL SCORE FOR THIS QUESTION: Exactly {total_points} Points.

EVALUATION CRITERIA & PROFESSOR'S GRADING PRINCIPLES:
1. STRICT REQUIREMENT FOR LABELS & EXPLANATIONS:
   - Naked calculations or unlabelled numbers do NOT qualify for full credit.
   - Students must clearly label what each calculated number represents (e.g., 'Current Year Tax Savings', 'Present Value of Next Year Savings').
   - If a computation is mathematically correct but unlabelled, or if a final decision lacks explanatory justification, deduct 10% to 25% of that specific milestone.
2. DYNAMIC POINT ALLOCATION (Total: {total_points} Points):
   - Analyze the provided Connect Master Solution and distribute the {total_points} points logically across the core computational milestones and the conceptual recommendation/justification.
3. CARRY-THROUGH ERROR PROTECTION:
   - If an early computational error occurs, penalize that line item once.
   - Do NOT double-penalize downstream steps if the student properly applied correct formulas and logical decision-making to their erroneous intermediate numbers.
4. REASONABLE ROUNDING:
   - Accept minor dollar differences resulting from rounded intermediate table factors.

INPUT DATA:
----------------------------------------
[QUESTION PROMPT]
{question_prompt}

[CONNECT MASTER SOLUTION]
{connect_solution}

[STUDENT SUBMISSION]
{student_submission}
----------------------------------------

OUTPUT FORMAT (STRICT):
SCORE: [X] / {total_points}

RUBRIC BREAKDOWN:
- Milestone 1: [Earned]/[Max] - [Brief explanation. Note if deductions occurred for missing labels]
- Milestone 2: [Earned]/[Max] - [Brief explanation]
- Milestone 3: [Earned]/[Max] - [Brief explanation]
- Milestone 4: [Earned]/[Max] - [Brief explanation]
- Recommendation & Justification: [Earned]/[Max] - [Brief explanation]

CONNECT FEEDBACK:
[Write 2 to 4 concise, professional, and encouraging sentences directly to the student. Highlight what was done correctly, point out missing labels, calculation errors, or incomplete justifications, and state the correct final values. This text will be pasted directly into McGraw-Hill Connect.]
"""
            try:
                # Calls the current standard flash model on the GenAI SDK
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                output = response.text

                st.divider()
                st.subheader("Grading Summary")

                if "CONNECT FEEDBACK:" in output:
                    breakdown, feedback = output.split("CONNECT FEEDBACK:", 1)
                    st.markdown(breakdown.strip())
                    
                    st.subheader("📋 Copyable Feedback for McGraw-Hill Connect")
                    st.text_area(
                        "Click the copy button in the top-right corner to paste into Connect:",
                        value=feedback.strip(),
                        height=150
                    )
                else:
                    st.markdown(output)

            except Exception as e:
                st.error(f"Error calling model: {e}")
