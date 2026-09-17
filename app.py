import os
import streamlit as st
from google import genai

# Streamlit Page Setup
st.set_page_config(
    page_title="Prof. Eagan's Grading Assist Tool | Purdue Daniels",
    page_icon="🚂",
    layout="wide"
)

# Purdue Old Gold & Black Styling
purdue_css = """
<style>
    /* Primary brand colors */
    :root {
        --purdue-gold: #CEB888;
        --purdue-dark-gold: #9D8249;
        --purdue-black: #000000;
        --purdue-gray: #373A36;
    }
    
    /* Header Accent */
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

    /* Buttons styled in Purdue Gold */
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

    /* Highlight Section Borders */
    .stTextArea textarea:focus {
        border-color: #CEB888 !important;
        box-shadow: 0 0 0 1px #CEB888 !important;
    }
</style>
"""
st.markdown(purdue_css, unsafe_allow_html=True)

# Purdue Branded Header Banner
st.markdown(
    """
    <div class="brand-banner">
        <h1>🚂 Prof. Eagan's Grading Assist Tool</h1>
        <p>Mitchell E. Daniels, Jr. School of Business • Connect Exam Evaluator (20 Points)</p>
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

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Question Prompt")
    question_prompt = st.text_area(
        "Paste McGraw-Hill Connect Question:",
        height=140,
        placeholder="Paste student's algorithmic problem statement..."
    )

    st.subheader("2. Connect Synthesized Solution")
    connect_solution = st.text_area(
        "Paste Connect Master Solution:",
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

TOTAL SCORE: Exactly 20 Points.

EVALUATION CRITERIA & PROFESSOR'S GRADING PRINCIPLES:
1. STRICT REQUIREMENT FOR LABELS & EXPLANATIONS:
   - Mere numbers or naked calculations are INSUFFICIENT for full credit.
   - Students must explicitly label what each calculated number represents (e.g., 'Present Value of Year 2 Savings', 'Current Year Tax Savings', etc.).
   - If a student shows the correct mathematical operation but leaves it unlabeled or provides no narrative reasoning for their conclusion, deduct 10% to 25% of that specific line item.
2. 20-POINT ALLOCATION:
   - Analyze the provided Connect Master Solution and map out its core conceptual steps into a clean 20-point distribution.
   - If this is the timing/present-value question, allocate:
     * Current Year Tax Savings: 4 pts (Calculation + clear label)
     * Next Year Nominal Savings: 4 pts (Calculation + clear label)
     * Present Value Application: 5 pts (Correct discount factor + label)
     * Net Incremental Savings: 3 pts (Comparison + label)
     * Final Timing Recommendation & Justification: 4 pts (Clear recommendation + narrative rationale)
   - If this is a different question, allocate the 20 points proportionally across its main computational and conceptual milestones.
3. CARRY-THROUGH ERROR PROTECTION:
   - If a student makes an early arithmetic error or selects an incorrect table factor, deduct points ONCE at that step.
   - Do NOT double-penalize downstream steps if the student properly applied the correct logic to their intermediate erroneous figure.
4. REASONABLE ROUNDING:
   - Accept minor dollar differences resulting from rounding intermediate discount factors.

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
SCORE: [X] / 20

RUBRIC BREAKDOWN:
- Milestone 1: [Earned]/[Max] - [Brief explanation. Note if points were lost for missing labels]
- Milestone 2: [Earned]/[Max] - [Brief explanation]
- Milestone 3: [Earned]/[Max] - [Brief explanation]
- Milestone 4: [Earned]/[Max] - [Brief explanation]
- Milestone 5: [Earned]/[Max] - [Brief explanation]

CONNECT FEEDBACK:
[Write 2 to 4 concise, professional, and encouraging sentences directly to the student. Highlight what was executed well, specifically point out missing labels, calculation errors, or incomplete justifications, and summarize the proper outcome. This will be pasted directly into Connect.]
"""
            try:
                # Using the stable 1.5 flash model
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
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
                        "Click the copy button in top right of this box to paste into Connect:",
                        value=feedback.strip(),
                        height=150
                    )
                else:
                    st.markdown(output)

            except Exception as e:
                st.error(f"Error calling model: {e}")
