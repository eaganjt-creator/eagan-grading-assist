import os
import streamlit as st
import streamlit.components.v1 as components
from google import genai

# Streamlit Page Setup
st.set_page_config(
    page_title="Prof. Eagan's Grading Assist Tool | Daniels School of Business",
    page_icon="🚂",
    layout="wide"
)

# Purdue Old Gold & Black Styling + Boilermaker Train Animation
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

    /* Boilermaker Train Track Animation */
    @keyframes chuggaChugga {
        0% { transform: translateX(-10%); }
        50% { transform: translateX(85%); }
        100% { transform: translateX(-10%); }
    }
    .train-container {
        width: 100%;
        overflow: hidden;
        background: #111111;
        border: 2px solid #CEB888;
        border-radius: 8px;
        padding: 14px 10px;
        margin: 15px 0;
        text-align: left;
    }
    .train-animation {
        display: inline-block;
        font-size: 2.2rem;
        animation: chuggaChugga 4s ease-in-out infinite;
    }
    .train-caption {
        color: #CEB888;
        font-weight: 600;
        font-size: 0.95rem;
        text-align: center;
        margin-top: 5px;
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
        # Boilermaker Special Train Animated Loader
        loader_placeholder = st.empty()
        loader_placeholder.markdown(
            """
            <div class="train-container">
                <div class="train-animation">🚂💨💨💨 🚃 🚃</div>
                <div class="train-caption">Boilermaker Special chugging through the rubric... Evaluating submission!</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        prompt = f"""
You are an expert tax accounting teaching assistant evaluating student exam submissions for Prof. Eagan at Purdue University's Daniels School of Business.

TOTAL SCORE FOR THIS QUESTION: Exactly {total_points} Points.

EVALUATION CRITERIA & PROFESSOR'S GRADING PRINCIPLES:
1. STRICT REQUIREMENT FOR LABELS & EXPLANATIONS:
   - Naked calculations or unlabelled numbers do NOT qualify for full credit.
   - Students must clearly label what each calculated number represents (e.g., 'Current Year Tax Savings', 'Present Value of Next Year Savings').
   - If a computation is mathematically correct but unlabelled, or if a final decision lacks explanatory justification, deduct 10% to 25% of that specific milestone.
2. DYNAMIC POINT ALLOCATION (Total: {total_points} Points):
   - Analyze the provided Connect Master Solution and distribute the {total_points} points logically across the computational milestones and the conceptual recommendation/justification.
3. CARRY-THROUGH ERROR PROTECTION:
   - If an early computational error occurs, penalize that line item once.
   - Do NOT double-penalize downstream steps if the student properly applied correct formulas and logical decision-making to their erroneous intermediate numbers.
4. REASONABLE ROUNDING:
   - Accept minor dollar differences resulting from rounded intermediate table factors.
5. TEST BANK / PUBLISHER SOLUTION SIMILARITY ANALYSIS:
   - Assess whether the student's submission displays unnatural or verbatim similarity to the Connect publisher solution wording (e.g., identical phrasing, matching parenthetical notes like '(i.e., assuming in one year)', or textbook-verbatim prose vs. typical authentic student wording).
   - Rate similarity concern as: Low (0-25%), Moderate (26-60%), or High (61-100%).

INPUT DATA:
----------------------------------------
[QUESTION PROMPT]
{question_prompt}

[CONNECT MASTER SOLUTION]
{connect_solution}

[STUDENT SUBMISSION]
{student_submission}
----------------------------------------

OUTPUT FORMAT (STRICT - PRESERVE LABELS EXACTLY):
SIMILARITY CONCERN LEVEL: [Low | Moderate | High] ([Percentage]%)
SIMILARITY NOTE: [1-2 sentences detailing whether the wording appears authentic or suspiciously copied from the solution manual/test bank.]

---STUDENT FEEDBACK BUNDLE---
TOTAL SCORE: [X] / {total_points}

RUBRIC BREAKDOWN:
- Milestone 1: [Earned]/[Max] - [Brief note. Specify if deductions occurred for missing labels]
- Milestone 2: [Earned]/[Max] - [Brief note]
- Milestone 3: [Earned]/[Max] - [Brief note]
- Milestone 4: [Earned]/[Max] - [Brief note]
- Recommendation & Justification: [Earned]/[Max] - [Brief note]

FEEDBACK SUMMARY:
[Write 2 to 3 concise, professional, and encouraging sentences directly to the student explaining strengths, specific mistakes, and correct targets.]
---END BUNDLE---
"""
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )
            output = response.text

            # Remove train loader once generated
            loader_placeholder.empty()

            st.divider()

            # Parse Similarity Meter & Feedback Bundle
            similarity_level = "Low"
            similarity_pct = 10
            similarity_note = "Wording appears authentic."
            bundle_text = output

            if "SIMILARITY CONCERN LEVEL:" in output:
                try:
                    level_line = [line for line in output.split("\n") if "SIMILARITY CONCERN LEVEL:" in line][0]
                    note_line = [line for line in output.split("\n") if "SIMILARITY NOTE:" in line][0]
                    similarity_note = note_line.replace("SIMILARITY NOTE:", "").strip()
                    
                    if "High" in level_line:
                        similarity_level = "High"
                        similarity_pct = 85
                    elif "Moderate" in level_line:
                        similarity_level = "Moderate"
                        similarity_pct = 50
                    else:
                        similarity_level = "Low"
                        similarity_pct = 15
                except Exception:
                    pass

            if "---STUDENT FEEDBACK BUNDLE---" in output:
                parts = output.split("---STUDENT FEEDBACK BUNDLE---")
                if len(parts) > 1:
                    bundle_text = parts[1].replace("---END BUNDLE---", "").strip()

            # Display Test Bank / Publisher Concern Meter
            st.subheader("🔍 Test Bank / Solution Similarity Gauge")
            col_meter, col_desc = st.columns([1, 2])
            with col_meter:
                if similarity_level == "High":
                    st.error(f"⚠️ Concern Level: {similarity_level} (~{similarity_pct}%)")
                elif similarity_level == "Moderate":
                    st.warning(f"⚡ Concern Level: {similarity_level} (~{similarity_pct}%)")
                else:
                    st.success(f"✅ Concern Level: {similarity_level} (~{similarity_pct}%)")
                st.progress(similarity_pct / 100.0)

            with col_desc:
                st.write(f"**Analysis:** {similarity_note}")
                if similarity_level in ["High", "Moderate"]:
                    st.caption("ℹ️ *TA Note: Verify if identical publisher phrasing or parentheticals were used.*")

            st.divider()

            # Student Feedback Section with Direct JavaScript Clipboard Copy Button
            st.subheader("📋 McGraw-Hill Connect Complete Feedback Package")
            st.caption("This bundle includes Score, Rubric Breakdown, and Narrative Feedback ready for Connect:")

            st.text_area(
                label="Complete Student Feedback",
                value=bundle_text,
                height=240,
                key="feedback_display"
            )

            # High-visibility Copy Button using JS Clipboard API
            escaped_bundle = bundle_text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
            copy_component = f"""
            <div>
                <button id="copyBtn" style="
                    background-color: #CEB888;
                    color: #000000;
                    font-weight: 700;
                    border: 2px solid #9D8249;
                    border-radius: 6px;
                    padding: 10px 18px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background 0.2s;">
                    📋 Copy Complete Feedback to Clipboard
                </button>
                <span id="copiedMsg" style="color: #CEB888; font-weight: bold; margin-left: 12px; display: none;">
                    ✓ Copied to clipboard!
                </span>
            </div>
            <script>
                document.getElementById('copyBtn').addEventListener('click', function() {{
                    navigator.clipboard.writeText(`{escaped_bundle}`).then(function() {{
                        const msg = document.getElementById('copiedMsg');
                        msg.style.display = 'inline';
                        setTimeout(() => {{ msg.style.display = 'none'; }}, 3500);
                    }});
                }});
            </script>
            """
            components.html(copy_component, height=55)

        except Exception as e:
            loader_placeholder.empty()
            st.error(f"Error calling model: {e}")
