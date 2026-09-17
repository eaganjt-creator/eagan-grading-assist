import os
import streamlit as st
import streamlit.components.v1 as components
from google import genai

# Streamlit Page Setup
st.set_page_config(
    page_title="Prof. Eagan's Grading Assist Tool | Purdue Daniels",
    page_icon="📋",
    layout="wide"
)

# Purdue Old Gold & Black Styling + Right-to-Left Locomotive Animation
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
        padding: 18px 24px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: white;
    }
    .brand-banner h1 {
        color: #CEB888 !important;
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
    }
    .brand-banner p {
        color: #E0E0E0;
        margin: 4px 0 0 0;
        font-size: 1.05rem;
    }

    /* Primary Gold Button */
    div.stButton > button[kind="primary"] {
        background-color: #CEB888 !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border: 2px solid #9D8249 !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #000000 !important;
        color: #CEB888 !important;
        border-color: #CEB888 !important;
    }

    /* Secondary/Clear Buttons */
    div.stButton > button[kind="secondary"] {
        background-color: transparent !important;
        color: #CEB888 !important;
        font-weight: 600 !important;
        border: 1px solid #CEB888 !important;
        border-radius: 6px !important;
        padding: 6px 14px !important;
        font-size: 0.85rem !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #373A36 !important;
        color: #FFFFFF !important;
    }

    /* Right-to-Left Full-Width Steam Locomotive Animation */
    @keyframes locomotiveRightToLeft {
        0% { transform: translateX(100vw); }
        100% { transform: translateX(-15vw); }
    }
    .train-container {
        width: 100%;
        overflow: hidden;
        background: #111111;
        border: 2px solid #CEB888;
        border-radius: 8px;
        padding: 16px 0;
        margin: 15px 0;
        white-space: nowrap;
    }
    .train-animation {
        display: inline-block;
        font-size: 2.6rem;
        will-change: transform;
        animation: locomotiveRightToLeft 4s linear infinite;
    }
    .train-caption {
        color: #CEB888;
        font-weight: 600;
        font-size: 0.95rem;
        text-align: center;
        margin-top: 6px;
    }
</style>
"""
st.markdown(purdue_css, unsafe_allow_html=True)

# Purdue University Daniels School of Business Banner
st.markdown(
    """
    <div class="brand-banner">
        <h1>Prof. Eagan's Grading Assist Tool</h1>
        <p>Purdue University Daniels School of Business</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------- SECURITY GATE -----------------
expected_password = os.environ.get("APP_PASSWORD") or st.secrets.get("APP_PASSWORD", None)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if expected_password and not st.session_state["authenticated"]:
    st.subheader("🔒 Access Restricted")
    pwd_input = st.text_input("Enter Access Password:", type="password")
    if st.button("Unlock Tool", type="primary"):
        if pwd_input == expected_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password. Access denied.")
    st.stop()
# --------------------------------------------------

# API Key Retrieval
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if not api_key:
    st.info("Please set GEMINI_API_KEY in Streamlit Secrets or sidebar to begin.", icon="🔑")
    st.stop()

client = genai.Client(api_key=api_key)

# Initialize session state keys for inputs
for key in ["prompt_input", "solution_input", "student_input", "evaluation_output"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# Clear Callbacks
def clear_prompt():
    st.session_state["prompt_input"] = ""

def clear_solution():
    st.session_state["solution_input"] = ""

def clear_student():
    st.session_state["student_input"] = ""

def clear_all():
    st.session_state["prompt_input"] = ""
    st.session_state["solution_input"] = ""
    st.session_state["student_input"] = ""
    st.session_state["evaluation_output"] = ""

# Point Scale Configuration
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
        placeholder="Paste student's algorithmic problem statement...",
        key="prompt_input"
    )
    st.button("Clear Question", type="secondary", on_click=clear_prompt, key="btn_clear_prompt")

    st.write("")
    st.subheader("2. Connect Master Solution")
    connect_solution = st.text_area(
        "Paste Connect Synthesized Solution:",
        height=180,
        placeholder="Paste Connect's generated answer and calculations...",
        key="solution_input"
    )
    st.button("Clear Master Solution", type="secondary", on_click=clear_solution, key="btn_clear_sol")

with col2:
    st.subheader("3. Student Submission")
    student_submission = st.text_area(
        "Paste Student Answer (Anonymized - No Names/IDs):",
        height=400,
        placeholder="Paste student response here...",
        key="student_input"
    )
    st.button("Clear Student Submission", type="secondary", on_click=clear_student, key="btn_clear_stud")

st.divider()

# Action Buttons: Evaluate & Reset All
btn_col1, btn_col2 = st.columns([3, 1])
with btn_col1:
    evaluate_btn = st.button("Evaluate Submission", type="primary", use_container_width=True)
with btn_col2:
    st.button("Reset / Clear All", type="secondary", on_click=clear_all, use_container_width=True)

if evaluate_btn:
    if not (question_prompt.strip() and connect_solution.strip() and student_submission.strip()):
        st.warning("Please paste all three fields before running evaluation.", icon="⚠️")
    else:
        # Animated Loader: Solo Steam Engine Chugging Right-to-Left
        loader_placeholder = st.empty()
        loader_placeholder.markdown(
            """
            <div class="train-container">
                <div class="train-animation">🚂</div>
                <div class="train-caption">Boilermaker Special evaluating submission against Connect rubric...</div>
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
   - Students must clearly label what each calculated number represents (e.g., 'Current Year Tax Savings', 'Recognized Gain', 'Present Value Factor').
   - If a computation is mathematically correct but unlabelled, or if a required conclusion lacks explanatory justification, deduct 10% to 25% of that specific milestone.
2. DYNAMIC MILESTONE BREAKDOWN (Total: {total_points} Points):
   - Analyze the provided Connect Master Solution and break the problem down into its natural logical milestones (typically between 2 to 6 milestones depending on the problem's scope).
   - Give each milestone a descriptive, informative name reflecting the actual tax or accounting milestone (do NOT use generic labels like 'Milestone 1').
   - Ensure the sum of the maximum points across all milestones equals EXACTLY {total_points} points.
   - Only include a 'Recommendation / Decision' milestone if the prompt explicitly asks for one.
3. CARRY-THROUGH ERROR PROTECTION:
   - If an early computational error occurs, penalize that milestone once.
   - Do NOT double-penalize downstream steps if the student properly applied correct formulas and logical decision-making to their erroneous intermediate numbers.
4. REASONABLE ROUNDING:
   - Accept minor dollar differences resulting from rounded intermediate table factors.
5. TEST BANK / PUBLISHER SOLUTION SIMILARITY ANALYSIS:
   - Assess whether the student's submission displays unnatural or verbatim similarity to the Connect publisher solution wording (e.g., identical phrasing, matching parenthetical notes, or textbook-verbatim prose vs. typical authentic student wording).
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
- [Descriptive Milestone Name]: [Earned]/[Max] - [Brief note. Specify if deductions occurred for missing labels or arithmetic errors]
- [Descriptive Milestone Name]: [Earned]/[Max] - [Brief note]
[Include remaining descriptive milestones so points sum exactly to {total_points}]

FEEDBACK SUMMARY:
[Write 2 to 3 concise, professional, and encouraging sentences directly to the student explaining strengths, specific mistakes, and correct targets.]
---END BUNDLE---
"""
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )
            st.session_state["evaluation_output"] = response.text
            loader_placeholder.empty()

        except Exception as e:
            loader_placeholder.empty()
            st.error(f"Error calling model: {e}")

# Render Evaluation Output
if st.session_state.get("evaluation_output"):
    output = st.session_state["evaluation_output"]
    st.divider()

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

    st.subheader("📋 McGraw-Hill Connect Complete Feedback Package")
    st.caption("This bundle includes Score, Rubric Breakdown, and Narrative Feedback ready for Connect:")

    st.text_area(
        label="Complete Student Feedback",
        value=bundle_text,
        height=240,
        key="feedback_display"
    )

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
