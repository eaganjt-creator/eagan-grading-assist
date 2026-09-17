import os
import re
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from google import genai

# Page Setup
st.set_page_config(
    page_title="Prof. Eagan's Grading Assist Tool | Purdue Daniels",
    page_icon="📋",
    layout="wide"
)

# Text Sanitizer to strip LaTeX/Greek symbols for clean Connect copy-pasting
def sanitize_latex(text: str) -> str:
    """Strips LaTeX wrappers, equations, and symbols to ensure clean plain text for Connect."""
    if not text:
        return ""
    # Common math symbols & operators
    text = text.replace(r"\Delta", "Change in ")
    text = text.replace(r"\times", " x ")
    text = text.replace(r"\cdot", " * ")
    text = text.replace(r"\approx", " approx. ")
    text = text.replace(r"\le", " <= ")
    text = text.replace(r"\ge", " >= ")
    text = text.replace(r"\neq", " != ")

    # Remove \text{...} wrappers -> ...
    text = re.sub(r"\\text\{([^}]+)\}", r"\1", text)

    # Remove \frac{A}{B} -> (A / B)
    text = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1 / \2)", text)

    # Remove math display delimiters like $(formula)$ -> (formula)
    text = re.sub(r"\$(\([^\$]+\))\$", r"\1", text)

    # Remove inline math syntax wrapping without touching regular currency like $24,000
    text = re.sub(r"\$([A-Za-z\s\+\-\*\/\=\(\)]+)\$", r"\1", text)

    # Clean leftover backslashes
    text = text.replace("\\", "")

    return text

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

    /* Secondary / Clear / Utility Buttons */
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

# Top Bar Controls
top_col1, top_col2, top_col3 = st.columns([1, 1.5, 2])
with top_col1:
    total_points = st.number_input(
        "Question Total Points:",
        min_value=1,
        max_value=100,
        value=20,
        step=1
    )
with top_col2:
    st.write("")
    st.write("")
    pin_questions = st.checkbox("📌 Pin Question & Master Solution", value=True, help="Prevents resetting Prompt and Solution when clearing submissions for the next student.")

# Initialize Session State
default_states = {
    "prompt_input": "",
    "solution_input": "",
    "student_input": "",
    "evaluation_output": "",
    "current_score": float(total_points),
    "original_ai_score": float(total_points),
    "similarity_level": "Low",
    "similarity_pct": 10,
    "similarity_note": "Awaiting evaluation.",
    "bundle_text": "",
    "base_bundle_text": "",
    "grading_log": [],
    "flagged_queue": []
}
for key, val in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Score Override Callback
def update_score_override():
    new_val = st.session_state["score_override_val"]
    orig_val = st.session_state.get("original_ai_score", new_val)
    bundle = st.session_state.get("base_bundle_text", "")
    
    if bundle:
        clean_bundle = re.sub(
            r"TOTAL SCORE:\s*[\d\.]+\s*/\s*[\d\.]+(\s*\[[^\]]+\])?",
            f"TOTAL SCORE: {new_val:g} / {total_points}",
            bundle
        )
        if abs(new_val - orig_val) >= 0.01:
            clean_bundle = re.sub(
                rf"TOTAL SCORE:\s*{new_val:g}\s*/\s*{total_points}",
                f"TOTAL SCORE: {new_val:g} / {total_points} [Note: Final score reflects manual grader discretion/adjustment from initial rubric assessment of {orig_val:g}/{total_points}]",
                clean_bundle
            )
        st.session_state["bundle_text"] = clean_bundle

# Callback Handlers
def clear_prompt():
    st.session_state["prompt_input"] = ""

def clear_solution():
    st.session_state["solution_input"] = ""

def clear_student():
    st.session_state["student_input"] = ""

def next_student_cleanup():
    st.session_state["student_input"] = ""
    st.session_state["evaluation_output"] = ""
    st.session_state["bundle_text"] = ""
    st.session_state["base_bundle_text"] = ""

def clear_all(pin_active):
    if not pin_active:
        st.session_state["prompt_input"] = ""
        st.session_state["solution_input"] = ""
    st.session_state["student_input"] = ""
    st.session_state["evaluation_output"] = ""
    st.session_state["bundle_text"] = ""
    st.session_state["base_bundle_text"] = ""

# Input Form
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

# Primary Action Buttons
btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])
with btn_col1:
    evaluate_btn = st.button("Evaluate Submission", type="primary", use_container_width=True)
with btn_col2:
    st.button("➡️ Next Student", type="secondary", on_click=next_student_cleanup, use_container_width=True, help="Clears student submission and output while keeping question and solution.")
with btn_col3:
    st.button("Reset / Clear All", type="secondary", on_click=lambda: clear_all(pin_questions), use_container_width=True)

# Run Evaluation
if evaluate_btn:
    if not (question_prompt.strip() and connect_solution.strip() and student_submission.strip()):
        st.warning("Please paste all three fields before running evaluation.", icon="⚠️")
    else:
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
   - Analyze the provided Connect Master Solution and break the problem down into its natural logical milestones (typically 2 to 6 milestones).
   - Give each milestone a descriptive, informative name reflecting the actual tax/accounting concept (do NOT use generic labels like 'Milestone 1').
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
6. STRICT PLAIN TEXT FORMATTING (NO LATEX OR MARKDOWN MATH):
   - Do NOT use LaTeX math equations, markup syntax, or backslashes under any circumstances (never output \\Delta, \\text{{}}, \\frac{{}}{{}}, or surround math with dollar signs).
   - Express all formulas in natural, clean keyboard plain text (e.g., write '(Change in Tax / Change in Income)' instead of LaTeX formulas). Connect does not support LaTeX rendering.

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
            raw_output = response.text
            st.session_state["evaluation_output"] = raw_output
            loader_placeholder.empty()

            # Parse similarity
            similarity_level = "Low"
            similarity_pct = 10
            similarity_note = "Wording appears authentic."
            bundle = raw_output

            if "SIMILARITY CONCERN LEVEL:" in raw_output:
                try:
                    level_line = [line for line in raw_output.split("\n") if "SIMILARITY CONCERN LEVEL:" in line][0]
                    note_line = [line for line in raw_output.split("\n") if "SIMILARITY NOTE:" in line][0]
                    similarity_note = note_line.replace("SIMILARITY NOTE:", "").strip()
                    if "High" in level_line:
                        similarity_level, similarity_pct = "High", 85
                    elif "Moderate" in level_line:
                        similarity_level, similarity_pct = "Moderate", 50
                    else:
                        similarity_level, similarity_pct = "Low", 15
                except Exception:
                    pass

            if "---STUDENT FEEDBACK BUNDLE---" in raw_output:
                parts = raw_output.split("---STUDENT FEEDBACK BUNDLE---")
                if len(parts) > 1:
                    bundle = parts[1].replace("---END BUNDLE---", "").strip()

            # Sanitize LaTeX
            bundle = sanitize_latex(bundle)

            # Extract numeric score awarded
            score_match = re.search(r"TOTAL SCORE:\s*([\d\.]+)\s*/", bundle)
            parsed_score = float(score_match.group(1)) if score_match else float(total_points)

            st.session_state["similarity_level"] = similarity_level
            st.session_state["similarity_pct"] = similarity_pct
            st.session_state["similarity_note"] = similarity_note
            st.session_state["base_bundle_text"] = bundle
            st.session_state["bundle_text"] = bundle
            st.session_state["current_score"] = parsed_score
            st.session_state["original_ai_score"] = parsed_score

            # Auto-record in Session Log
            timestamp_str = datetime.now().strftime("%I:%M:%S %p")
            st.session_state["grading_log"].append({
                "Timestamp": timestamp_str,
                "Awarded": parsed_score,
                "Max": total_points,
                "Similarity": f"{similarity_level} ({similarity_pct}%)",
                "Feedback Snippet": (bundle[:110] + "...") if len(bundle) > 110 else bundle
            })

        except Exception as e:
            loader_placeholder.empty()
            st.error(f"Error calling model: {e}")

# Render Evaluation Output Area
if st.session_state.get("evaluation_output"):
    st.divider()

    # Similarity Concern Display
    st.subheader("🔍 Test Bank / Solution Similarity Gauge")
    col_meter, col_desc = st.columns([1, 2])
    with col_meter:
        sim_lvl = st.session_state["similarity_level"]
        sim_pct = st.session_state["similarity_pct"]
        if sim_lvl == "High":
            st.error(f"⚠️ Concern Level: {sim_lvl} (~{sim_pct}%)")
        elif sim_lvl == "Moderate":
            st.warning(f"⚡ Concern Level: {sim_lvl} (~{sim_pct}%)")
        else:
            st.success(f"✅ Concern Level: {sim_lvl} (~{sim_pct}%)")
        st.progress(sim_pct / 100.0)

    with col_desc:
        st.write(f"**Analysis:** {st.session_state['similarity_note']}")
        if sim_lvl in ["High", "Moderate"]:
            st.caption("ℹ️ *TA Note: Check for exact publisher phrasing or textbook solution parentheticals.*")

    st.divider()

    # Score Adjustment Override & Prof Review Flag
    adj_col1, adj_col2 = st.columns([2, 2])
    with adj_col1:
        st.number_input(
            "Final Score Override (adjusts copyable text automatically):",
            min_value=0.0,
            max_value=float(total_points),
            value=float(st.session_state["current_score"]),
            step=0.5,
            key="score_override_val",
            on_change=update_score_override
        )
    with adj_col2:
        st.write("")
        st.write("")
        if st.button("🚩 Flag for Prof. Eagan Review", type="secondary"):
            current_override = st.session_state.get("score_override_val", st.session_state["current_score"])
            flag_entry = {
                "Timestamp": datetime.now().strftime("%I:%M:%S %p"),
                "Score": f"{current_override} / {total_points}",
                "Submission Excerpt": st.session_state.get("student_input", "")[:250] + "...",
                "Note": "Flagged by TA for professor check."
            }
            st.session_state["flagged_queue"].append(flag_entry)
            st.toast("Submission flagged for Prof. Eagan!", icon="🚩")

    # Current bundle reflecting reactive overrides + note
    active_bundle = st.session_state["bundle_text"]

    # Copyable Student Feedback
    st.subheader("📋 McGraw-Hill Connect Feedback Package")
    st.caption("Score, Rubric Breakdown, and Student Feedback ready for Connect:")

    st.text_area(
        label="Complete Student Feedback",
        value=active_bundle,
        height=240
    )

    # Direct JavaScript Clipboard Copy
    escaped_bundle = active_bundle.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
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

# Session Log & Flagged Queue at Bottom
st.divider()
exp_log, exp_flag = st.columns(2)

with exp_log:
    with st.expander(f"📊 Session Grading Audit Log ({len(st.session_state['grading_log'])} Graded)"):
        if st.session_state["grading_log"]:
            df_log = pd.DataFrame(st.session_state["grading_log"])
            st.dataframe(df_log, use_container_width=True)
            csv_data = df_log.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Session Grading Log (.csv)",
                data=csv_data,
                file_name=f"grading_session_log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                type="secondary"
            )
        else:
            st.caption("No submissions graded yet this session.")

with exp_flag:
    with st.expander(f"🚩 Flagged for Prof. Eagan ({len(st.session_state['flagged_queue'])} Items)"):
        if st.session_state["flagged_queue"]:
            for idx, item in enumerate(st.session_state["flagged_queue"]):
                st.markdown(f"**#{idx+1} [{item['Timestamp']}] Score: {item['Score']}**")
                st.text(item["Submission Excerpt"])
                st.markdown("---")
        else:
            st.caption("No edge-case submissions currently flagged.")
