import json
import os
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime
from html import escape

import streamlit as st
import streamlit.components.v1 as components

from agents import (
    CoachAgent, EvidenceAgent, GroqGateway, InterviewerAgent,
    ResearchAgent, StrategyAgent,
)
from db import init_db, save_session
from report import build_markdown_report, build_pdf_report
from utils import extract_uploaded_text, safe_clamp


st.set_page_config(
    page_title="Intervia — AI Interview Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

CATEGORIES = [
    "Behavioral & Situational 🎭",
    "Technical & Role-Specific 💻",
    "HR & Screening Basics 🤝",
    "Leadership & Management 👔",
    "Case & Analytical Interviews 📊",
    "Competency & Skill-Based 🧠",
    "Reverse Interviewing — Questions for the Employer 🔍",
]
DURATIONS = {"30 Minutes": 30, "60 Minutes": 60, "120 Minutes": 120, "180 Minutes": 180}
TARGET_QUESTIONS = {30: 8, 60: 15, 120: 28, 180: 40}

# ---------------------------- Ultra-premium dashboard theme ----------------------------
st.markdown("""
<style>
/* ================================================================
   INTERVIA // ULTRA PREMIUM EXECUTIVE DARK UI
   Theme: InterviewAI Studio Cockpit aesthetic
   ================================================================ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root{
 --bg:#0E1117;
 --bg2:#12151C;
 --panel:#171A22;
 --panel2:#1A1D24;
 --panel3:#14171E;
 --line:#2D313A;
 --line2:#3B4252;
 --text:#E2E8F0;
 --text2:#C9D4E6;
 --muted:#64748B;
 --muted2:#94A3B8;
 --purple:#8B5CF6;
 --purple2:#A78BFA;
 --indigo:#6366F1;
 --violet:#A855F7;
 --cyan:#22D3EE;
 --green:#10B981;
 --green2:#34D399;
 --yellow:#FBBF24;
 --red:#EF4444;
 --red2:#F87171;
 --blue:#3B82F6;
 --blue2:#60A5FA;
}

*{box-sizing:border-box}
html,body{
 background:var(--bg)!important;
 font-family:'Inter',sans-serif!important;
}
.stApp{
 background:var(--bg)!important;
 color:var(--text)!important;
 font-family:'Inter',sans-serif!important;
}
html, body, [class*="css"] {
 font-family: 'Inter', sans-serif;
}

.block-container{padding:10px 18px 20px!important;max-width:1560px!important}

/* Hide Streamlit default header/footer */
header {visibility: hidden;}
footer {visibility: hidden;}

/* Sidebar */
[data-testid="stSidebar"]{
 background:var(--bg2)!important;
 border-right:1px solid #1F2937!important;
 padding-top:20px;
}
[data-testid="stSidebar"] *{color:var(--text2)}
[data-testid="stSidebar"] .stButton button{background:#1A202C!important}
[data-testid="stSidebar"] .stMarkdown{margin-bottom:3px!important}
[data-testid="stSidebar"] hr{border-color:#1F2937!important}

/* Form labels */
label,[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label{
 color:var(--muted2)!important;font-weight:600!important;font-size:11px!important;letter-spacing:.02em!important;
}
[data-testid="stCaptionContainer"] p,.stCaption{color:#7F8DA5!important;font-size:10px!important}

/* Inputs */
input,textarea,[data-baseweb="input"] input,[data-baseweb="textarea"] textarea{
 color:var(--text)!important;
 -webkit-text-fill-color:var(--text)!important;
 background:#12151C!important;
 border-color:#2D313A!important;
 border-radius:8px!important;
}
input::placeholder,textarea::placeholder{color:#64748B!important;-webkit-text-fill-color:#64748B!important}

[data-baseweb="select"]>div{
 background:#12151C!important;border-color:#2D313A!important;color:var(--text)!important;border-radius:8px!important;
}
[data-baseweb="select"] span{color:var(--text)!important}
[data-baseweb="popover"] *{color:var(--text)!important}
[data-baseweb="menu"]{background:#171A22!important;border:1px solid #2D313A!important}
[data-baseweb="menu"] *{color:var(--text)!important}

[data-baseweb="radio"] label,[data-baseweb="checkbox"] label{color:var(--text2)!important}

[data-testid="stFileUploader"] section{
 background:#12151C!important;border:1px dashed #3B4252!important;padding:10px!important;border-radius:8px!important;
}
[data-testid="stFileUploader"] section *{color:var(--muted2)!important}

[data-testid="stExpander"]{
 background:#14171E!important;border:1px solid #2D313A!important;border-radius:12px!important;
}
[data-testid="stExpander"] summary{color:var(--text2)!important;font-size:11px!important}

hr{border-color:#1F2937!important;margin:7px 0!important}

/* Native tabs */
div[data-baseweb="tab-list"]{
 display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr));gap:4px!important;
 background:#12151C!important;padding:4px!important;border:1px solid #1F2937!important;border-radius:12px!important;
}
button[data-baseweb="tab"]{
 min-height:32px!important;height:32px!important;padding:4px 8px!important;border-radius:8px!important;
 color:var(--muted2)!important;font-size:10px!important;font-weight:700!important;white-space:nowrap!important;
}
button[data-baseweb="tab"][aria-selected="true"]{
 background:linear-gradient(90deg,rgba(139,92,246,.30),rgba(99,102,241,.18))!important;
 color:#FFFFFF!important;border:1px solid rgba(139,92,246,.42)!important;
 box-shadow:0 4px 16px rgba(139,92,246,.18)!important;
}

/* Buttons */
div[data-testid="stButton"]>button,.stDownloadButton>button{
 min-height:36px!important;height:auto!important;padding:8px 12px!important;
 border-radius:8px!important;border:1px solid #4A5568!important;background:#1A202C!important;
 color:var(--text)!important;font-size:11px!important;font-weight:600!important;
 transition:all .3s ease!important;
}
div[data-testid="stButton"]>button:hover,.stDownloadButton>button:hover{
 border-color:var(--purple)!important;
 color:#FFFFFF!important;
 box-shadow:0 0 10px rgba(139,92,246,.3)!important;
}
div[data-testid="stButton"]>button[kind="primary"]{
 background:linear-gradient(90deg,#6366F1,#A855F7)!important;
 color:#FFFFFF!important;border:none!important;
 box-shadow:0 4px 15px rgba(139,92,246,.35)!important;
}
div[data-testid="stButton"]>button[kind="primary"]:hover{
 box-shadow:0 0 15px rgba(168,85,247,.5)!important;
}

/* ===================== Custom Classes ===================== */

/* Metric cards */
.metric-card{
 background:linear-gradient(145deg,#1A1D24,#14171E)!important;
 border:1px solid #2D313A!important;
 border-radius:12px!important;
 padding:12px 14px!important;
 min-height:72px!important;
 box-shadow:0 4px 6px -1px rgba(0,0,0,.5)!important;
 transition:all .25s ease!important;
}
.metric-card:hover{
 border-color:#3B4252!important;
 box-shadow:0 4px 16px rgba(139,92,246,.12)!important;
}
.metric-k{
 font-size:10px!important;letter-spacing:.08em!important;text-transform:uppercase;
 color:#64748B!important;font-weight:600!important;
}
.metric-v{
 font-size:22px!important;font-weight:700!important;
 background:linear-gradient(135deg,#A78BFA,#22D3EE);
 -webkit-background-clip:text;-webkit-text-fill-color:transparent;
 background-clip:text;
 margin-top:3px!important;line-height:1.05!important;
}
.metric-s{font-size:10px!important;color:#94A3B8!important;margin-top:2px!important}
.metric-s.sub-class{color:#10B981!important}

/* Topbar */
.topbar{
 display:flex;justify-content:space-between;align-items:center;
 border-bottom:1px solid #1F2937;
 padding:4px 1px 10px;margin-bottom:10px;min-height:36px;
}
.brand{font-weight:700;letter-spacing:.02em;font-size:15px;color:#E2E8F0!important}
.brand span{color:#A78BFA!important}
.crumb{color:#64748B!important;font-size:11px;font-weight:500}

/* Chips */
.chip{
 display:inline-block;
 border:1px solid #4A5568;
 background:#2D3748;
 color:#A0AEC0;
 border-radius:999px;
 padding:4px 10px;
 font-size:10px;
 font-weight:600;
 margin-left:5px;
 line-height:1.2;
 text-transform:uppercase;
 letter-spacing:.5px;
}
.chip.lav{color:#A78BFA;border-color:#8B5CF6;background:rgba(139,92,246,.2)}
.chip.green{color:#34D399;border-color:#10B981;background:rgba(16,185,129,.2)}
.chip.red{color:#F87171;border-color:#EF4444;background:rgba(239,68,68,.2)}

/* Nav row */
.navrow{
 display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:6px;
 background:#12151C;border:1px solid #1F2937;border-radius:12px;padding:6px;margin-bottom:12px;
}
.navpill{
 padding:9px 6px;border-radius:8px;color:#94A3B8;font-size:10px;font-weight:600;
 white-space:nowrap;text-align:center;overflow:hidden;text-overflow:ellipsis;
 cursor:pointer;border:1px solid transparent;transition:all .2s ease;
}
.navpill:hover{color:#FFFFFF;background:rgba(139,92,246,.08)}
.navpill.active{
 background:linear-gradient(90deg,#6366F1,#A855F7);
 color:#FFFFFF;
 box-shadow:0 4px 15px rgba(139,92,246,.35);
}

/* Hero */
.hero2{
 padding:20px 24px;border:1px solid #3B4252;border-left:4px solid #8B5CF6;border-radius:12px;
 background:linear-gradient(145deg,#1A1D24,#14171E);
 box-shadow:0 4px 6px -1px rgba(0,0,0,.5);margin-bottom:12px;
}
.hero2 h1{
 font-size:26px!important;line-height:1.1!important;margin:6px 0!important;
 letter-spacing:-.025em!important;color:#E2E8F0!important;font-weight:700!important;
}
.eyebrow{
 font-size:10px;color:#A78BFA;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
}
.subhero{color:#94A3B8;font-size:12px;max-width:980px;line-height:1.5}

/* Panel */
.panel{
 background:linear-gradient(145deg,#171A22,#14171E);
 border:1px solid #2D313A;border-radius:12px;padding:16px!important;
 box-shadow:0 4px 6px -1px rgba(0,0,0,.5);
 margin-bottom:12px!important;
}
.panel-title{
 font-size:11px;letter-spacing:.08em;text-transform:uppercase;
 color:#E2E8F0!important;font-weight:700;margin-bottom:8px;
}
.panel-sub{font-size:11px;color:#94A3B8!important;line-height:1.5}

/* Question card */
.question-card{
 padding:20px!important;
 border:1px solid #3B4252;border-left:4px solid #8B5CF6;border-radius:12px;
 background:linear-gradient(145deg,#1A1D24,#14171E);
 box-shadow:0 4px 6px -1px rgba(0,0,0,.5);
}
.question-card .q{
 font-size:20px!important;line-height:1.4!important;font-weight:600!important;color:#E2E8F0!important;
}

/* Category pill */
.category-pill{
 display:inline-block;padding:5px 10px;border:1px solid #8B5CF6;border-radius:999px;
 color:#A78BFA;background:rgba(139,92,246,.2);
 font-size:10px;font-weight:600;margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px;
}

/* Status rows */
.status-row{
 display:flex;justify-content:space-between;align-items:center;
 border-bottom:1px solid #1F2937;padding:8px 0;
}
.status-row:last-child{border-bottom:0}
.status-name{font-size:12px;font-weight:500;color:#E2E8F0!important}
.status-badge{
 font-size:10px;font-weight:600;letter-spacing:.05em;border-radius:999px;padding:4px 10px;
 border:1px solid #10B981;color:#34D399;background:rgba(16,185,129,.2);text-transform:uppercase;
}
.status-badge.active{border-color:#8B5CF6;color:#A78BFA;background:rgba(139,92,246,.2)}
.status-badge.wait{border-color:#FBBF24;color:#FBBF24;background:rgba(251,191,36,.15)}
.status-badge.off{border-color:#4A5568;color:#A0AEC0;background:#2D3748}

/* Evidence KPI */
.evidence-kpi{
 background:linear-gradient(145deg,#1A1D24,#14171E);
 border:1px solid #2D313A;border-radius:10px;padding:10px 12px!important;
}
.evidence-kpi .k{
 font-size:9px;color:#64748B;text-transform:uppercase;letter-spacing:.08em;font-weight:600;
}
.evidence-kpi .v{
 font-size:20px;font-weight:700;margin-top:3px;
 color:#A78BFA;
}

/* Score ring */
.score-ring{
 border-radius:12px;padding:16px;
 background:linear-gradient(145deg,#1A1D24,#14171E);
 border:1px solid #2D313A;
 box-shadow:0 4px 6px -1px rgba(0,0,0,.5);
}

/* Feedback items */
.feedback-item{
 padding:10px 12px;
 border-left:3px solid #8B5CF6;
 background:rgba(139,92,246,.06);
 border-radius:0 8px 8px 0;
 margin:6px 0;
 color:#C9D4E6!important;
 font-size:12px;line-height:1.5;
}

.smallnote{font-size:10px;color:#64748B!important;line-height:1.4}
.footer{
 padding:12px 3px 2px;color:#64748B;text-align:center;font-size:10px;
 border-top:1px solid #1F2937;margin-top:20px;
}

/* Progress bars */
.stProgress{margin:6px 0!important}
.stProgress>div>div{height:8px!important;background:#2D3748!important;border-radius:4px!important}
.stProgress>div>div>div{
 background:linear-gradient(90deg,#6366F1,#22D3EE)!important;border-radius:4px!important;
}

/* Metrics */
[data-testid="stMetricValue"]{
 font-size:22px!important;color:#E2E8F0!important;font-weight:700!important;
}
[data-testid="stMetricLabel"]{
 font-size:11px!important;color:#94A3B8!important;
}
[data-testid="stMetricDelta"]{font-size:10px!important}

[data-testid="stHorizontalBlock"]{gap:.5rem!important}
[data-testid="stVerticalBlock"]{gap:.4rem!important}
.stTextInput,.stTextArea,.stSelectbox,.stMultiSelect,.stRadio,.stCheckbox,.stSlider,.stFileUploader{margin-bottom:4px!important}

/* Responsive */
@media (max-width:1100px){
 .block-container{padding-left:12px!important;padding-right:12px!important}
 .navrow{grid-template-columns:repeat(3,minmax(0,1fr))}
 .topbar{gap:8px;align-items:flex-start}
 .topbar>div:last-child{max-width:58%;text-align:right}
 .hero2 h1{font-size:22px!important}
}
@media (max-width:720px){
 .navrow{grid-template-columns:repeat(2,minmax(0,1fr))}
 .topbar{display:block}
 .topbar>div:last-child{max-width:100%;text-align:left;margin-top:6px}
 .chip{margin-left:0;margin-right:4px}
 .hero2{padding:14px}
 .question-card .q{font-size:18px!important}
}
</style>
""", unsafe_allow_html=True)

# ---------------------------- Helpers ----------------------------
def configured_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, default) or "").strip()


def render_speech_controls(text: str, key: str, title: str, language: str, autoplay: bool = False):
    payload = json.dumps(text or "", ensure_ascii=False)
    lang_payload = json.dumps(language or "en-US")
    safe_key = re.sub(r"[^A-Za-z0-9_]", "_", key)
    delay = 450 if autoplay else 999999
    components.html(f"""
    <div style="font-family:Arial,sans-serif;padding:5px 0">
      <span style="color:#7F8DA6;font-size:10px;font-weight:800;letter-spacing:.08em">{escape(title).upper()}</span>
      <button id="p_{safe_key}" style="margin-left:12px;border:1px solid #34425F;background:#141D31;color:#fff;border-radius:9px;padding:7px 12px">▶ Play</button>
      <button id="s_{safe_key}" style="border:1px solid #2C3852;background:#0C1424;color:#AAB7CD;border-radius:9px;padding:7px 12px">■ Stop</button>
      <span id="m_{safe_key}" style="color:#7F8DA6;font-size:10px;margin-left:8px"></span>
    </div>
    <script>
    const t_{safe_key}={payload}, l_{safe_key}={lang_payload}, p_{safe_key}=document.getElementById('p_{safe_key}'), s_{safe_key}=document.getElementById('s_{safe_key}'), m_{safe_key}=document.getElementById('m_{safe_key}');
    function stop_{safe_key}(){{if('speechSynthesis' in window) speechSynthesis.cancel();m_{safe_key}.textContent='Stopped';}}
    function play_{safe_key}(){{if(!('speechSynthesis' in window)){{m_{safe_key}.textContent='Browser speech unavailable';return;}}stop_{safe_key}();let u=new SpeechSynthesisUtterance(t_{safe_key});u.lang=l_{safe_key};u.rate=.96;u.onstart=()=>m_{safe_key}.textContent='Speaking…';u.onend=()=>m_{safe_key}.textContent='Question finished';u.onerror=()=>m_{safe_key}.textContent='Playback failed';speechSynthesis.speak(u);}}
    p_{safe_key}.onclick=play_{safe_key};s_{safe_key}.onclick=stop_{safe_key};setTimeout(()=>{{if({str(autoplay).lower()})play_{safe_key}();}},{delay});
    </script>
    """, height=55, scrolling=False)


def render_timer(started_at: float, duration_minutes: int):
    remaining = max(0, int(duration_minutes * 60 - (time.time() - started_at)))
    components.html(f"""
    <div style="text-align:right;font-family:Arial,sans-serif">
      <span style="font-size:9px;color:#7D8AA2;font-weight:900;letter-spacing:.12em">SESSION TIME REMAINING</span>
      <div id="tm" style="font-size:22px;color:#EEF2FF;font-weight:900">--:--</div>
    </div>
    <script>
    let r={remaining},e=document.getElementById('tm');function t(){{let m=Math.floor(Math.max(0,r)/60),s=Math.max(0,r)%60;e.textContent=String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');r--;}}t();setInterval(t,1000);
    </script>
    """, height=55, scrolling=False)


def duration_state(started_at: float, duration_minutes: int):
    elapsed = max(0.0, time.time() - started_at)
    remaining = max(0.0, duration_minutes * 60 - elapsed)
    return elapsed, remaining, remaining <= 0


def question_target(duration_minutes: int, elapsed_seconds: float, completed: int) -> int:
    base = TARGET_QUESTIONS[duration_minutes]
    if elapsed_seconds <= 0:
        return base
    avg_turn = elapsed_seconds / max(1, completed)
    projected = int((duration_minutes * 60) / max(avg_turn, 120))
    return max(3, min(base * 2, max(base, projected)))


def speech_metrics(text: str, estimated_seconds: float | None = None):
    words = re.findall(r"\b[\w']+\b", text or "")
    filler_list = ["um", "uh", "erm", "like", "you know", "basically", "actually", "sort of", "kind of"]
    lowered = (text or "").lower()
    fillers = sum(len(re.findall(r"\b" + re.escape(f) + r"\b", lowered)) for f in filler_list)
    seconds = estimated_seconds or max(10, len(words) / 2.3) if words else 0
    return {
        "words": len(words),
        "filler_words": fillers,
        "estimated_seconds": round(seconds, 1),
        "words_per_minute": round(len(words) / (seconds / 60), 1) if seconds else 0,
    }


def metric_card(label, value, sub="", sub_class=""):
    return f"""<div class="metric-card"><div class="metric-k">{escape(str(label))}</div><div class="metric-v">{escape(str(value))}</div><div class="metric-s {sub_class}">{escape(str(sub))}</div></div>"""


def reset_session():
    for key, val in {
        "session_id": str(uuid.uuid4()), "evidence": None, "research": None, "turns": [],
        "question": None, "started": False, "started_at": None, "session_duration": 30,
        "question_mode": "Text Questions", "answer_mode": "⌨️ Type Answers",
        "categories": CATEGORIES[:], "company": "", "company_track": "", "camera_enabled": False,
        "groq_model": "", "session_complete": False, "last_plan": None
    }.items():
        st.session_state[key] = val


init_db()
defaults = {
    "session_id": str(uuid.uuid4()), "evidence": None, "research": None, "turns": [],
    "question": None, "started": False, "started_at": None, "session_duration": 30,
    "question_mode": "Text Questions", "answer_mode": "⌨️ Type Answers",
    "categories": CATEGORIES[:], "company": "", "company_track": "", "camera_enabled": False,
    "groq_model": "", "session_complete": False, "last_plan": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------- Sidebar ----------------------------
with st.sidebar:
    st.markdown("### 🎯 Intervia")
    st.caption("STUDIO COCKPIT • AI INTERVIEW INTELLIGENCE")
    st.markdown('<div class="smallnote">Evidence-grounded • adaptive • professional session telemetry</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("**TARGET PROFILE**")
    target_role = st.text_input("Target job position", value="Senior Backend Software Engineer", disabled=st.session_state.started)
    company = st.text_input("Company / employer (optional)", value=st.session_state.company, disabled=st.session_state.started)

    st.markdown("**PERSONA MODEL**")
    persona = st.radio("Persona", ["FAANG-Style", "Friendly", "Strict Exec", "Startup CTO"], horizontal=True, disabled=st.session_state.started, label_visibility="collapsed")

    st.markdown("**EVALUATION VECTOR**")
    mode = st.selectbox("Primary vector", ["Mixed", "Technical", "Behavioral", "Case / Situational", "HR / Screening", "Leadership"], disabled=st.session_state.started)
    categories = st.multiselect("Interview categories", CATEGORIES, default=st.session_state.categories, disabled=st.session_state.started)

    st.markdown("**ADAPTIVE ESCALATION**")
    difficulty = st.select_slider("Difficulty baseline", ["Foundation", "Standard", "Hard", "Ultra Hard"], value="Standard", disabled=st.session_state.started)

    st.markdown("**CONTEXT INGESTION**")
    st.caption("CV + JD remain the candidate-grounding source. External research is a separate evidence class.")

    st.markdown("**SESSION DESIGN**")
    duration_label = st.selectbox("Practice session duration", list(DURATIONS.keys()), index=list(DURATIONS.values()).index(st.session_state.session_duration), disabled=st.session_state.started)
    question_mode = st.radio("Question format", ["Text Questions", "Audio Questions"], index=0 if st.session_state.question_mode == "Text Questions" else 1, horizontal=True, disabled=st.session_state.started)
    answer_mode = st.radio("Answer format", ["⌨️ Type Answers", "🎙️ Speak Answers"], index=0 if st.session_state.answer_mode.startswith("⌨") else 1, horizontal=True, disabled=st.session_state.started)
    use_research = st.checkbox("Current role/company research", value=False, disabled=st.session_state.started)
    camera_enabled = st.checkbox("Presentation snapshot", value=st.session_state.camera_enabled, disabled=st.session_state.started)
    speech_language = st.selectbox("Question voice", ["English (US)", "English (UK)"], disabled=st.session_state.started)
    speech_locale = "en-US" if speech_language == "English (US)" else "en-GB"
    answer_length = st.selectbox("Practice-answer length", ["Short", "Standard", "Detailed"], disabled=st.session_state.started)

    st.divider()
    api_key = st.text_input("Groq API key", type="password", value=configured_secret("GROQ_API_KEY"), help="For Streamlit Cloud, use st.secrets instead of committing keys.")
    if not st.session_state.started:
        st.session_state.session_duration = DURATIONS[duration_label]
        st.session_state.question_mode = question_mode
        st.session_state.answer_mode = answer_mode
        st.session_state.categories = categories or CATEGORIES[:]
        st.session_state.company = company
        st.session_state.camera_enabled = camera_enabled

# ---------------------------- Top shell ----------------------------
model_label = st.session_state.get("groq_model") or "AUTO MODEL"
st.markdown(f"""
<div class="topbar">
  <div><span class="brand">InterviewAI <span>STUDIO COCKPIT</span></span><span class="crumb">&nbsp; / &nbsp;Workspace / Session Telemetry</span></div>
  <div>
    <span class="chip lav">{escape(model_label)}</span>
    <span class="chip green">Evidence Grounded</span>
    <span class="chip">{escape(persona)}</span>
    <span class="chip">{escape(difficulty)} Track</span>
  </div>
</div>
<div class="navrow">
  <div class="navpill active">1. Live Adaptive Interview</div>
  <div class="navpill">2. 6-D Evaluation</div>
  <div class="navpill">3. JD → Curriculum</div>
  <div class="navpill">4. Resume & ATS Gap</div>
  <div class="navpill">5. Live Coding IDE</div>
  <div class="navpill">6. Executive Performance</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero2">
  <div class="eyebrow">AI INTERVIEW • SMARTER YOU</div>
  <h1>Premium adaptive interview cockpit.</h1>
  <div class="subhero">Realistic hiring-manager questions grounded in your CV and Job Description, with adaptive escalation, voice/text practice, ATS readiness, and a complete professional report after every session.</div>
</div>
""", unsafe_allow_html=True)

# KPI strip
ev = st.session_state.evidence or {}
ats = ev.get("ats_readiness", {})
k1, k2, k3, k4, k5 = st.columns(5)
k1.markdown(metric_card("TARGET ROLE", target_role, "Profile locked at start"), unsafe_allow_html=True)
k2.markdown(metric_card("ATS READINESS", f"{ats.get('score', '--')}/100", ats.get("band", "Build evidence first")), unsafe_allow_html=True)
k3.markdown(metric_card("INTERVIEW PROGRESS", f"{len(st.session_state.turns)}", f"of ~{TARGET_QUESTIONS[st.session_state.session_duration]} core questions"), unsafe_allow_html=True)
latest_score = st.session_state.turns[-1]["feedback"].get("overall", 0) if st.session_state.turns else 0
k4.markdown(metric_card("LATEST SCORE", f"{latest_score}/100", "Coach evaluation" if st.session_state.turns else "No answer scored yet"), unsafe_allow_html=True)
k5.markdown(metric_card("AGENT STATUS", "5 / 5", "Logical agent system ready"), unsafe_allow_html=True)

# ---------------------------- Evidence ingestion ----------------------------
left, right = st.columns([1.42, 1], gap="medium")
with left:
    st.markdown('<div class="panel"><div class="panel-title">Candidate Evidence Intelligence</div><div class="panel-sub">Upload the candidate CV/Resume and Job Description. The ATS check is a deterministic readiness heuristic; it does not certify any vendor ATS.</div></div>', unsafe_allow_html=True)
    cv_file = st.file_uploader("CV / Resume", type=["pdf", "docx", "txt"], key="cv")
    jd_file = st.file_uploader("Job Description", type=["pdf", "docx", "txt"], key="jd")
    jd_text = st.text_area("Or paste the Job Description", height=120, placeholder="Paste the job description if you do not have a file.")
    company_track = st.text_area("Optional public company/role context", height=75, placeholder="Add factual, public context if desired. This is never converted into candidate evidence.", disabled=st.session_state.started)

    b1, b2 = st.columns([1.2, 1])
    with b1:
        build_evidence = st.button("⚡ Build Evidence + ATS Intelligence", type="primary", use_container_width=True, disabled=st.session_state.started)
    with b2:
        if st.button("↺ New Session", use_container_width=True):
            reset_session()
            st.rerun()

    if build_evidence:
        if not api_key:
            st.error("Enter a Groq API key first.")
        elif not cv_file:
            st.error("Upload a CV / Resume.")
        elif not (jd_file or jd_text.strip()):
            st.error("Upload or paste the Job Description.")
        else:
            st.session_state.company_track = company_track
            cv_text = extract_uploaded_text(cv_file)
            final_jd = extract_uploaded_text(jd_file) if jd_file else jd_text
            st.session_state.evidence = EvidenceAgent().build(
                cv_text=safe_clamp(cv_text, 14000),
                jd_text=safe_clamp(final_jd, 12000),
                target_role=target_role,
                industry="Not specified — grounded in CV/JD and role context",
            )
            st.session_state.research = None
            st.session_state.turns = []
            st.session_state.question = None
            st.session_state.started = False
            st.session_state.session_complete = False
            st.session_state.started_at = None
            if use_research:
                try:
                    gateway = GroqGateway(api_key)
                    st.session_state.research = ResearchAgent(gateway).run(
                        target_role, "Not specified — grounded in CV/JD and role context",
                        safe_clamp(final_jd, 6000), company=company, company_track=company_track
                    )
                except Exception:
                    st.warning("Optional current role/company research is unavailable. The interview will continue with CV/JD evidence.")
            st.success("Evidence pack created. Candidate evidence, JD requirements, ATS signals and optional research remain separated.")

with right:
    st.markdown('<div class="panel"><div class="panel-title">5-Agent Mission Control</div>', unsafe_allow_html=True)
    statuses = [
        ("Evidence Intelligence", "READY" if st.session_state.evidence else "WAIT"),
        ("Research Intelligence", "READY" if st.session_state.research else ("OPTIONAL" if not use_research else "WAIT")),
        ("Adaptive Strategy", "ACTIVE" if st.session_state.started else "READY"),
        ("AI Interviewer", "ACTIVE" if st.session_state.question else "READY"),
        ("Performance Coach", "READY" if st.session_state.started or st.session_state.turns else "STANDBY"),
    ]
    for name, status in statuses:
        cls = "active" if status == "ACTIVE" else "wait" if status == "WAIT" else "off" if status in ("OPTIONAL","STANDBY") else ""
        st.markdown(f'<div class="status-row"><span class="status-name">{escape(name)}</span><span class="status-badge {cls}">{status}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.evidence:
    ev = st.session_state.evidence
    ats = ev.get("ats_readiness", {})
    st.markdown('<div class="panel"><div class="panel-title">Evidence Control Center</div>', unsafe_allow_html=True)
    ec1, ec2, ec3, ec4, ec5 = st.columns(5)
    ec1.markdown(f'<div class="evidence-kpi"><div class="k">Candidate facts</div><div class="v">{len(ev.get("candidate_facts", []))}</div></div>', unsafe_allow_html=True)
    ec2.markdown(f'<div class="evidence-kpi"><div class="k">JD requirements</div><div class="v">{len(ev.get("jd_requirements", []))}</div></div>', unsafe_allow_html=True)
    ec3.markdown(f'<div class="evidence-kpi"><div class="k">JD matches</div><div class="v">{len(ev.get("matches", []))}</div></div>', unsafe_allow_html=True)
    ec4.markdown(f'<div class="evidence-kpi"><div class="k">Skill gaps</div><div class="v">{len(ev.get("gaps", []))}</div></div>', unsafe_allow_html=True)
    ec5.markdown(f'<div class="evidence-kpi"><div class="k">ATS score</div><div class="v">{ats.get("score", 0)}/100</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("ATS readiness details — parser/keyword/formatting heuristic"):
        st.write(f"**Band:** {ats.get('band', 'Not calculated')}")
        for check in ats.get("checks", []):
            st.write(f"**{check['name']} — {check['score']}/100 — {check['status']}**")
            st.caption(check["detail"])
        if ats.get("keyword_gaps"):
            st.write("**JD terms to review:**", ", ".join(ats["keyword_gaps"]))
        if ats.get("recommendations"):
            st.write("**Recommendations:**")
            for item in ats["recommendations"]:
                st.write("• " + item)

    with st.expander("Evidence ledger — candidate facts vs JD requirements"):
        st.write("**Candidate evidence (CV only)**")
        st.write(ev.get("candidate_facts", []))
        st.write("**JD requirements (not candidate facts)**")
        st.write(ev.get("jd_requirements", []))
        st.write("**Grounding matches**")
        st.write(ev.get("matches", []))
        st.write("**Unknowns / gaps**")
        st.write(ev.get("gaps", []))

    if not st.session_state.started and not st.session_state.session_complete:
        if st.button("🚀 START ULTRA ADAPTIVE INTERVIEW", type="primary", use_container_width=True):
            if not categories:
                st.error("Select at least one interview category.")
            elif not api_key:
                st.error("Groq API key is required.")
            else:
                try:
                    gateway = GroqGateway(api_key)
                    st.session_state.groq_model = gateway.selected_model()
                    strategy = StrategyAgent()
                    interviewer = InterviewerAgent(gateway)
                    now = time.time()
                    st.session_state.started_at = now
                    elapsed, remaining, _ = duration_state(now, st.session_state.session_duration)
                    target_count = question_target(st.session_state.session_duration, elapsed, 0)
                    plan = strategy.plan([], mode, duration_label, ev, categories=categories, remaining_minutes=round(remaining/60, 1), target_questions=target_count)
                    st.session_state.last_plan = plan
                    q = interviewer.ask_question(ev, st.session_state.research, plan, target_role, "Not specified", mode, company=company)
                    st.session_state.question = q
                    st.session_state.started = True
                    st.session_state.session_complete = False
                    st.rerun()
                except Exception:
                    st.error("The adaptive interview could not start. Check the Groq key, model access and network, then retry.")

# ---------------------------- Live interview studio ----------------------------
if st.session_state.started and st.session_state.question:
    st.markdown('<div class="panel"><div class="panel-title">Live Adaptive Interview • Session Telemetry</div>', unsafe_allow_html=True)
    elapsed, remaining, expired = duration_state(st.session_state.started_at, st.session_state.session_duration)
    turn_no = len(st.session_state.turns) + 1
    target_count = question_target(st.session_state.session_duration, elapsed, len(st.session_state.turns))
    progress = min(1.0, len(st.session_state.turns) / max(1, target_count))
    p1, p2, p3 = st.columns([1.7, .7, .8])
    with p1:
        st.progress(progress, text=f"Question {turn_no} of adaptive target • {escape(difficulty)} escalation track")
    with p2:
        st.metric("Elapsed", f"{int(elapsed//60):02d}:{int(elapsed%60):02d}")
    with p3:
        render_timer(st.session_state.started_at, st.session_state.session_duration)
    st.markdown('</div>', unsafe_allow_html=True)

    if expired:
        st.warning("⏱️ Session time reached zero. Your complete session report is ready below.")
        st.session_state.question = None
        st.session_state.session_complete = True
    else:
        q_obj = st.session_state.question if isinstance(st.session_state.question, dict) else {"category": "Adaptive", "question": str(st.session_state.question)}
        question_text = q_obj.get("question", "").strip()
        category = q_obj.get("category", "Adaptive")
        st.markdown(f'<div class="question-card"><div class="category-pill">{escape(category)}</div><div class="q">{escape(question_text)}</div></div>', unsafe_allow_html=True)
        render_speech_controls(question_text, f"q_{turn_no}", "Generated hiring-manager question", speech_locale, autoplay=question_mode=="Audio Questions")
        if question_mode == "Audio Questions":
            st.caption("Audio mode uses browser speech synthesis. Browser autoplay policies may require one manual Play click.")

        aleft, aright = st.columns([1.45, 1])
        with aleft:
            st.markdown("#### Candidate response")
            answer = ""
            voice_transcript = ""
            audio = None
            if answer_mode == "⌨️ Type Answers":
                answer = st.text_area("Your answer", key=f"answer_{turn_no}", height=190, placeholder="Answer naturally. Use concrete examples, decisions, trade-offs and outcomes.")
            else:
                audio = st.audio_input("🎙️ Record your answer", sample_rate=16000, key=f"audio_{turn_no}")
                st.caption("Near-real-time turn-based voice: record → transcribe → coach. Continuous WebRTC streaming is a future enhancement.")
            camera = st.camera_input("Optional presentation snapshot", key=f"cam_{turn_no}") if camera_enabled else None
        with aright:
            st.markdown("#### Active evaluation focus")
            plan = st.session_state.last_plan or {}
            focus = plan.get("focus", "High-signal role-specific baseline")
            st.markdown(f'<div class="score-ring"><div class="metric-k">CURRENT STRATEGY</div><div class="metric-v" style="font-size:20px">{escape(focus.title())}</div><div class="smallnote">Weakest dimension: {escape(plan.get("weakest_dimension","relevance"))}</div><br/><div class="smallnote">Candidate evidence is locked to CV facts. JD requirements guide questions but never become candidate history.</div></div>', unsafe_allow_html=True)
            st.markdown('<div class="smallnote" style="margin-top:10px">VOICE / TEXT • ROLE-SPECIFIC • ADAPTIVE</div>', unsafe_allow_html=True)

        submit = st.button("✨ SUBMIT ANSWER & CALIBRATE NEXT QUESTION", type="primary", use_container_width=True)
        if submit:
            elapsed_now, remaining_now, expired_now = duration_state(st.session_state.started_at, st.session_state.session_duration)
            if expired_now:
                st.session_state.question = None
                st.session_state.session_complete = True
                st.rerun()
            elif not api_key:
                st.error("Groq API key is required.")
            else:
                gateway = GroqGateway(api_key)
                if answer_mode == "🎙️ Speak Answers" and audio is not None:
                    try:
                        voice_transcript = gateway.transcribe(audio.getvalue(), getattr(audio, "name", "answer.wav")).strip()
                        answer = voice_transcript
                    except Exception:
                        st.error("Voice transcription failed. Please record again or switch to text.")
                else:
                    answer = (answer or "").strip()

                if not answer:
                    st.error("Provide an answer before submitting.")
                else:
                    try:
                        coach = CoachAgent(gateway)
                        result = coach.evaluate(question_text, answer, st.session_state.evidence, target_role, mode, answer_length)
                        metrics = speech_metrics(answer) if voice_transcript else {
                            "words": len(answer.split()), "filler_words": None, "estimated_seconds": None, "words_per_minute": None
                        }
                        camera_feedback = None
                        if camera is not None:
                            try:
                                camera_feedback = gateway.analyze_camera(camera.getvalue(), getattr(camera, "type", "image/jpeg"))
                            except Exception:
                                camera_feedback = {"available": False, "message": "Presentation snapshot analysis unavailable."}
                        result["speech_metrics"] = metrics
                        result["presentation_cues"] = camera_feedback
                        turn = {
                            "question": question_text,
                            "category": category,
                            "answer": answer,
                            "answer_mode": "voice" if voice_transcript else "text",
                            "voice_transcript": voice_transcript,
                            "feedback": result,
                            "timestamp": datetime.now().isoformat(timespec="seconds"),
                            "elapsed_seconds": round(elapsed_now, 1),
                            "strategy": st.session_state.last_plan or {},
                        }
                        st.session_state.turns.append(turn)
                        save_session(st.session_state.session_id, target_role, "Not specified", st.session_state.turns)

                        elapsed_after, remaining_after, expired_after = duration_state(st.session_state.started_at, st.session_state.session_duration)
                        if expired_after:
                            st.session_state.question = None
                            st.session_state.session_complete = True
                        else:
                            strategy = StrategyAgent()
                            target_count = question_target(st.session_state.session_duration, elapsed_after, len(st.session_state.turns))
                            plan = strategy.plan(
                                st.session_state.turns, mode, duration_label, st.session_state.evidence,
                                categories=st.session_state.categories, remaining_minutes=round(remaining_after/60,1),
                                target_questions=target_count
                            )
                            st.session_state.last_plan = plan
                            interviewer = InterviewerAgent(gateway)
                            try:
                                st.session_state.question = interviewer.ask_question(
                                    st.session_state.evidence, st.session_state.research, plan,
                                    target_role, "Not specified", mode, company=company
                                )
                            except Exception:
                                st.session_state.question = None
                                st.session_state.session_complete = True
                                st.warning("The answer was saved, but the next adaptive question could not be generated. The session report is still available.")
                        st.rerun()
                    except Exception:
                        st.error("Coaching failed for this turn. The app kept your evidence state; retry the answer or end the session.")

# ---------------------------- Latest feedback + report ----------------------------
if st.session_state.turns:
    latest = st.session_state.turns[-1]["feedback"]
    st.markdown('<div class="panel"><div class="panel-title">AI Feedback • 6-D Evaluation</div>', unsafe_allow_html=True)
    cols = st.columns(7)
    keys = ["technical", "relevance", "evidence", "communication", "structure", "confidence"]
    labels = ["Technical", "Relevance", "Evidence", "Communication", "Structure", "Confidence"]
    for col, key, label in zip(cols[:6], keys, labels):
        col.metric(label, latest.get("scores", {}).get(key, 0))
    cols[6].metric("Overall", latest.get("overall", 0))
    st.markdown('<div class="panel" style="margin-top:8px">', unsafe_allow_html=True)
    f1, f2 = st.columns(2)
    with f1:
        st.markdown("**Strengths**")
        for x in latest.get("strengths", [])[:5]:
            st.markdown(f'<div class="feedback-item">✓ {escape(x)}</div>', unsafe_allow_html=True)
        st.markdown("**Missing / improve**")
        for x in latest.get("missing_points", [])[:5]:
            st.markdown(f'<div class="feedback-item">△ {escape(x)}</div>', unsafe_allow_html=True)
    with f2:
        st.markdown("**Verification notes**")
        for x in latest.get("verification_notes", [])[:5]:
            st.markdown(f'<div class="feedback-item">⌁ {escape(x)}</div>', unsafe_allow_html=True)
        st.markdown("**Suggested better practice answer**")
        st.markdown(f'<div class="feedback-item">{escape(latest.get("practice_answer",""))}</div>', unsafe_allow_html=True)
        st.markdown("**Next improvement**")
        st.markdown(f'<div class="feedback-item">{escape(latest.get("next_improvement",""))}</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    if st.session_state.started and st.button("⏹ END SESSION & FINALIZE PROFESSIONAL REPORT", use_container_width=True):
        st.session_state.question = None
        st.session_state.started = False
        st.session_state.session_complete = True
        st.rerun()

    st.markdown('<div class="panel"><div class="panel-title">Final Session Intelligence</div>', unsafe_allow_html=True)
    category_scores = defaultdict(list)
    for t in st.session_state.turns:
        category_scores[t.get("category", "General")].append(t.get("feedback", {}).get("overall", 0))
    if category_scores:
        readiness = st.columns(min(4, len(category_scores)))
        for i, (cat, vals) in enumerate(category_scores.items()):
            readiness[i % len(readiness)].metric(cat.split(" ")[0], round(sum(vals)/len(vals)))
    st.markdown("**Report coverage**")
    st.caption("Every configured session input and every generated output is captured, including Speech analytics when voice is used: profile, mode, duration, categories, evidence/ATS, research, question, answer, score dimensions, strengths, missing points, verification notes, better answer, next improvement, speech metrics and presentation cues.")
    st.markdown('</div>', unsafe_allow_html=True)

    md = build_markdown_report(
        target_role=target_role,
        industry="Not specified — grounded in CV/JD and role context",
        mode=mode,
        turns=st.session_state.turns,
        evidence=st.session_state.evidence,
        duration_minutes=st.session_state.session_duration,
        question_mode=st.session_state.question_mode,
        answer_mode=st.session_state.answer_mode,
        categories=st.session_state.categories,
        company=company,
        research=st.session_state.research,
        model=st.session_state.groq_model or "Automatic model discovery",
        session_id=st.session_state.session_id,
        started_at=st.session_state.started_at,
    )
    pdf = build_pdf_report(
        target_role=target_role,
        industry="Not specified — grounded in CV/JD and role context",
        mode=mode,
        turns=st.session_state.turns,
        evidence=st.session_state.evidence,
        duration_minutes=st.session_state.session_duration,
        question_mode=st.session_state.question_mode,
        answer_mode=st.session_state.answer_mode,
        categories=st.session_state.categories,
        company=company,
        research=st.session_state.research,
        model=st.session_state.groq_model or "Automatic model discovery",
        session_id=st.session_state.session_id,
        started_at=st.session_state.started_at,
    )
    r1, r2 = st.columns(2)
    r1.download_button("⬇ Download complete Markdown report", md, file_name="intervia_premium_session_report.md", mime="text/markdown", use_container_width=True)
    r2.download_button("⬇ Download complete PDF report", pdf, file_name="intervia_premium_session_report.pdf", mime="application/pdf", use_container_width=True)

st.markdown('<div class="footer">INTERVIA • Evidence-grounded interview practice • ATS readiness heuristic • 5 logical agents • Voice + text • Professional session reporting</div>', unsafe_allow_html=True)
