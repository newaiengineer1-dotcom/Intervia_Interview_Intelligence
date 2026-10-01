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
    CoachAgent,
    EvidenceAgent,
    GroqGateway,
    InterviewerAgent,
    ResearchAgent,
    StrategyAgent,
)
from db import init_db, save_session
from report import build_markdown_report, build_pdf_report
from utils import extract_uploaded_text, safe_clamp


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Intervia — Interview Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# INTERVIEW OPTIONS
# ============================================================

CATEGORIES = [
    "Behavioral & Situational 🎭",
    "Technical & Role-Specific 💻",
    "HR & Screening Basics 🤝",
    "Leadership & Management 👔",
    "Case & Analytical Interviews 📊",
    "Competency & Skill-Based 🧠",
    "Reverse Interviewing — Questions for the Employer 🔍",
]

INTERVIEW_MODES = [
    "Mixed",
    "Technical",
    "Behavioral",
    "Case / Situational",
    "HR / Screening",
    "Leadership",
]

DURATIONS = {
    "30 Minutes": 30,
    "60 Minutes": 60,
    "120 Minutes": 120,
    "180 Minutes": 180,
}

TARGET_QUESTIONS = {
    30: 8,
    60: 15,
    120: 28,
    180: 40,
}


# ============================================================
# DARK AI DASHBOARD CSS
# ============================================================

st.markdown(
    """
    <style>

    :root {
        --bg: #050b16;
        --bg2: #091326;
        --panel: #0e1a30;
        --panel2: #12213c;
        --line: #2b4168;
        --text: #f4f7ff;
        --text2: #d8e2f4;
        --muted: #b5c2d8;
        --accent: #8b6cff;
        --accent2: #a78bfa;
        --good: #6ee7b7;
        --warning: #fbbf24;
        --danger: #fb7185;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 80% 0%,
                rgba(87, 64, 180, 0.35) 0%,
                transparent 34%
            ),
            linear-gradient(
                135deg,
                var(--bg) 0%,
                #071224 55%,
                #08152a 100%
            );

        color: var(--text);
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #071020 0%,
                #09152a 100%
            );

        border-right: 1px solid #263b60;
    }

    [data-testid="stSidebar"] * {
        color: var(--text2);
    }

    html,
    body,
    [class*="css"] {
        color: var(--text);
    }

    p,
    span,
    label,
    li {
        color: var(--text2);
    }

    .stMarkdown,
    .stCaption,
    .stText,
    .stTextInput,
    .stTextArea {
        color: var(--text);
    }

    [data-testid="stCaptionContainer"] p {
        color: #b8c6dc !important;
        font-size: 0.9rem;
    }

    /* ========================================================
       HERO
       ======================================================== */

    .hero {
        padding: 30px 34px;
        border: 1px solid #334b78;
        border-radius: 24px;

        background:
            linear-gradient(
                135deg,
                rgba(124, 92, 255, 0.30),
                rgba(10, 23, 45, 0.95)
            );

        box-shadow:
            0 20px 60px rgba(0, 0, 0, 0.38);

        margin-bottom: 24px;
    }

    .eyebrow {
        color: #c4b5fd !important;
        font-size: 13px;
        font-weight: 900;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    .hero h1 {
        color: #ffffff !important;
        margin: 8px 0;
        font-size: 40px;
        line-height: 1.15;
    }

    .hero .muted {
        color: #c8d4e8 !important;
        font-size: 16px;
        line-height: 1.6;
    }

    /* ========================================================
       CARDS
       ======================================================== */

    .card {
        padding: 20px;
        border: 1px solid #2d4369;
        border-radius: 18px;
        background: rgba(14, 26, 48, 0.92);
        margin-bottom: 14px;
        color: var(--text);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.20);
    }

    /* ========================================================
       AGENT COCKPIT
       ======================================================== */

    .agent-cockpit {
        padding: 20px;
        border: 1px solid #2d4369;
        border-radius: 18px;
        background: rgba(14, 26, 48, 0.92);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.20);
    }

    .cockpit-title {
        color: #ffffff !important;
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 14px;
    }

    .agent {
        display: flex;
        justify-content: space-between;
        align-items: center;

        padding: 13px 4px;

        border-bottom: 1px solid #263957;

        color: #e7eefb;
    }

    .agent:last-child {
        border-bottom: 0;
    }

    .agent-name {
        color: #f4f7ff !important;
        font-weight: 650;
    }

    .status {
        color: var(--good) !important;
        background: #123d30;
        border: 1px solid #256b52;
        border-radius: 999px;

        padding: 4px 9px;

        font-size: 11px;
        font-weight: 800;
    }

    .status.ready {
        color: #6ee7b7 !important;
    }

    .status.optional {
        color: #fde68a !important;
        background: #4a3510;
        border-color: #795d19;
    }

    .status.waiting {
        color: #cbd5e1 !important;
        background: #243044;
        border-color: #40516d;
    }

    .status.active {
        color: #ddd6fe !important;
        background: #35276f;
        border-color: #6951d7;
    }

    /* ========================================================
       QUESTION
       ======================================================== */

    .question {
        font-size: 25px;
        line-height: 1.45;
        font-weight: 750;

        padding: 24px;

        border-left: 5px solid var(--accent);

        background:
            linear-gradient(
                135deg,
                #0c1930,
                #101f3a
            );

        border-radius: 16px;

        color: #ffffff !important;

        box-shadow:
            0 10px 30px rgba(0, 0, 0, 0.25);
    }

    .category {
        display: inline-block;

        padding: 7px 12px;

        border: 1px solid #536b99;

        border-radius: 999px;

        color: #e7ddff !important;

        font-size: 12px;
        font-weight: 700;

        background: #17264a;

        margin-bottom: 10px;
    }

    .small {
        font-size: 12px;
        color: #b9c7dd !important;
    }

    .muted {
        color: #b9c7dd !important;
    }

    /* ========================================================
       INPUTS
       ======================================================== */

    .stSelectbox label,
    .stMultiSelect label,
    .stTextInput label,
    .stTextArea label,
    .stRadio label,
    .stCheckbox label,
    .stFileUploader label {
        color: #edf3ff !important;
        font-weight: 700 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #111f38 !important;
        border: 1px solid #3c5278 !important;
        color: #ffffff !important;
    }

    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }

    div[data-baseweb="input"] {
        background-color: #101e35 !important;
        border: 1px solid #3c5278 !important;
    }

    div[data-baseweb="input"] input {
        color: #ffffff !important;
        background-color: #101e35 !important;
    }

    textarea {
        color: #ffffff !important;
        background-color: #101e35 !important;
        border: 1px solid #3c5278 !important;
    }

    textarea::placeholder,
    input::placeholder {
        color: #91a3bf !important;
    }

    span[data-baseweb="tag"] {
        background-color: #4c3aa8 !important;
        color: #ffffff !important;
    }

    span[data-baseweb="tag"] span {
        color: #ffffff !important;
    }

    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {
        background: linear-gradient(
            135deg,
            #7657f6,
            #5b42d8
        ) !important;

        color: #ffffff !important;

        border: 1px solid #927cff !important;

        border-radius: 12px !important;

        font-weight: 800 !important;

        min-height: 44px;

        box-shadow:
            0 8px 20px rgba(80, 60, 180, 0.30);
    }

    .stButton > button:hover {
        background: linear-gradient(
            135deg,
            #8a6cff,
            #684fe6
        ) !important;

        color: #ffffff !important;

        border-color: #b1a1ff !important;
    }

    /* ========================================================
       TABS
       ======================================================== */

    button[data-baseweb="tab"] {
        color: #b9c7dd !important;
        font-weight: 700 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
    }

    [data-baseweb="tab-highlight"] {
        background-color: #8b6cff !important;
    }

    /* ========================================================
       METRICS
       ======================================================== */

    [data-testid="stMetricLabel"] {
        color: #b9c7dd !important;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    [data-testid="stMetricDelta"] {
        color: #6ee7b7 !important;
    }

    /* ========================================================
       EXPANDERS / ALERTS
       ======================================================== */

    [data-testid="stExpander"] {
        background-color: #0d1a31 !important;
        border: 1px solid #2e456c !important;
        border-radius: 14px !important;
    }

    [data-testid="stExpander"] summary {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    [data-testid="stAlert"] {
        color: #f4f7ff !important;
    }

    [data-testid="stAlert"] p {
        color: #f4f7ff !important;
    }

    hr {
        border-color: #2b4168 !important;
    }

    .timer {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff !important;
    }

    .mode-box {
        padding: 14px;

        border: 1px solid #30476d;

        border-radius: 14px;

        background: #0b172c;

        color: #eaf1ff !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def configured_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""

    return str(value or os.getenv(name, default) or "").strip()


def friendly_groq_error(exc: Exception) -> str:
    message = str(exc)

    if "403" in message and "Access denied" in message:
        return (
            "Groq returned HTTP 403: Access denied. "
            "Check the Groq API key and Streamlit Cloud Secrets. "
            "If the same key works locally but not on Streamlit Cloud, "
            "the deployed environment may be blocked from reaching Groq."
        )

    if "429" in message or "rate limit" in message.lower():
        return (
            "Groq rate limit reached. Wait about one minute and retry. "
            "Avoid repeatedly pressing the AI buttons."
        )

    return message


def render_speech_controls(
    text: str,
    key: str,
    title: str,
    language: str,
    autoplay: bool = False,
):
    payload = json.dumps(text or "", ensure_ascii=False)
    lang_payload = json.dumps(language or "en-US")

    safe_key = re.sub(
        r"[^A-Za-z0-9_]",
        "_",
        key,
    )

    autoplay_code = "speak()" if autoplay else ""

    components.html(
        f"""
        <div style="
            font-family:Arial,sans-serif;
            padding:8px 0;
            color:#d8e2f4;
        ">

            <div style="
                color:#b9c7dd;
                font-size:12px;
                font-weight:700;
                margin-bottom:7px;
            ">
                🔊 {escape(title)}
            </div>

            <button
                id="play_{safe_key}"
                style="
                    border:1px solid #526b96;
                    background:#17264a;
                    color:#fff;
                    border-radius:10px;
                    padding:9px 14px;
                    cursor:pointer;
                    margin-right:6px;
                "
            >
                ▶ Play
            </button>

            <button
                id="stop_{safe_key}"
                style="
                    border:1px solid #526b96;
                    background:#0d1830;
                    color:#d8e2f4;
                    border-radius:10px;
                    padding:9px 14px;
                    cursor:pointer;
                "
            >
                ■ Stop
            </button>

            <span
                id="status_{safe_key}"
                style="
                    color:#aebed5;
                    font-size:12px;
                    margin-left:8px;
                "
            ></span>
        </div>

        <script>
        const speechText = {payload};
        const speechLang = {lang_payload};

        const playButton =
            document.getElementById("play_{safe_key}");

        const stopButton =
            document.getElementById("stop_{safe_key}");

        const statusElement =
            document.getElementById("status_{safe_key}");

        function stopSpeech(label) {{
            if ("speechSynthesis" in window) {{
                window.speechSynthesis.cancel();
            }}

            statusElement.textContent = label || "Stopped";
        }}

        function speak() {{
            if (!("speechSynthesis" in window)) {{
                statusElement.textContent =
                    "Browser speech is not supported.";
                return;
            }}

            window.speechSynthesis.cancel();

            const utterance =
                new SpeechSynthesisUtterance(speechText);

            utterance.lang = speechLang;
            utterance.rate = 0.96;
            utterance.pitch = 1.0;

            utterance.onstart = function() {{
                statusElement.textContent = "Speaking…";
            }};

            utterance.onend = function() {{
                statusElement.textContent =
                    "Question finished";
            }};

            utterance.onerror = function() {{
                statusElement.textContent =
                    "Speech playback failed";
            }};

            window.speechSynthesis.speak(utterance);
        }}

        playButton.onclick = speak;

        stopButton.onclick = function() {{
            stopSpeech("Stopped");
        }};

        {autoplay_code}
        </script>
        """,
        height=78,
        scrolling=False,
    )


def render_timer(
    started_at: float,
    duration_minutes: int,
):
    remaining = max(
        0,
        int(
            duration_minutes * 60
            - (time.time() - started_at)
        ),
    )

    components.html(
        f"""
        <div style="
            padding:8px 0;
            text-align:right;
            font-family:Arial,sans-serif;
        ">

            <span style="
                color:#b9c7dd;
                font-size:12px;
                font-weight:700;
            ">
                SESSION TIME REMAINING
            </span>

            <div
                id="timer"
                style="
                    font-size:24px;
                    font-weight:800;
                    color:#fff;
                "
            >
                --:--
            </div>
        </div>

        <script>
        let remaining = {remaining};

        const timer =
            document.getElementById("timer");

        function updateTimer() {{
            const minutes =
                Math.floor(
                    Math.max(0, remaining) / 60
                );

            const seconds =
                Math.max(0, remaining) % 60;

            timer.textContent =
                String(minutes).padStart(2, "0")
                + ":"
                + String(seconds).padStart(2, "0");

            if (remaining <= 0) {{
                timer.textContent =
                    "00:00 — TIME";
            }}

            remaining -= 1;
        }}

        updateTimer();

        setInterval(
            updateTimer,
            1000
        );
        </script>
        """,
        height=70,
        scrolling=False,
    )


def duration_state(
    started_at: float,
    duration_minutes: int,
):
    elapsed = max(
        0.0,
        time.time() - started_at,
    )

    remaining = max(
        0.0,
        duration_minutes * 60 - elapsed,
    )

    return (
        elapsed,
        remaining,
        remaining <= 0,
    )


def question_target(
    duration_minutes: int,
    elapsed_seconds: float,
    completed: int,
) -> int:

    base = TARGET_QUESTIONS[duration_minutes]

    if elapsed_seconds <= 0:
        return base

    average_turn =
        elapsed_seconds / max(
            1,
            completed,
        )

    projected = int(
        (duration_minutes * 60)
        / max(
            average_turn,
            120,
        )
    )

    return max(
        3,
        min(
            base * 2,
            max(
                base,
                projected,
            ),
        ),
    )


def speech_metrics(
    text: str,
    estimated_seconds=None,
):

    words = re.findall(
        r"\b[\w']+\b",
        text or "",
    )

    filler_list = [
        "um",
        "uh",
        "erm",
        "like",
        "you know",
        "basically",
        "actually",
        "sort of",
        "kind of",
    ]

    lowered = (text or "").lower()

    fillers = sum(
        len(
            re.findall(
                r"\b"
                + re.escape(item)
                + r"\b",
                lowered,
            )
        )
        for item in filler_list
    )

    word_count = len(words)

    if estimated_seconds:
        seconds = estimated_seconds
    elif word_count:
        seconds = max(
            10,
            word_count / 2.3,
        )
    else:
        seconds = 0

    wpm = (
        round(
            word_count
            / (seconds / 60),
            1,
        )
        if seconds
        else 0
    )

    return {
        "words": word_count,
        "filler_words": fillers,
        "estimated_seconds": round(
            seconds,
            1,
        ),
        "words_per_minute": wpm,
    }


# ============================================================
# DATABASE
# ============================================================

init_db()


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "session_id": str(uuid.uuid4()),
    "evidence": None,
    "research": None,
    "turns": [],
    "question": None,
    "started": False,
    "started_at": None,
    "session_duration": 30,
    "question_mode": "Text Questions",
    "answer_mode": "⌨️ Type Answers",
    "categories": CATEGORIES[:],
    "company": "",
    "company_track": "",
    "camera_enabled": False,
    "api_key": "",
    "target_role": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# GROQ API KEY
# ============================================================

secret_api_key = configured_secret(
    "GROQ_API_KEY"
)

if secret_api_key:
    st.session_state.api_key = secret_api_key

elif not st.session_state.api_key:
    st.session_state.api_key = os.getenv(
        "GROQ_API_KEY",
        "",
    ).strip()


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">

        <div class="eyebrow">
            Adaptive Interview Intelligence
        </div>

        <h1>
            Practice against the job —
            <br>
            with text or voice.
        </h1>

        <div class="muted">
            Build your evidence pack, select an interview mode
            and categories, then practice with an adaptive AI interviewer.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GROQ API KEY UI
# ============================================================

with st.expander(
    "🔐 Groq API Configuration",
    expanded=not bool(
        st.session_state.api_key
    ),
):

    st.markdown(
        "### Groq API Key"
    )

    st.caption(
        "Enter your Groq API key here for this session. "
        "For Streamlit Cloud, you can also store GROQ_API_KEY "
        "in Streamlit Secrets."
    )

    entered_api_key = st.text_input(
        "Groq API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="gsk_...",
        help="Your key is used only for Groq API requests.",
    )

    if entered_api_key.strip():

        st.session_state.api_key = (
            entered_api_key.strip()
        )

        st.success(
            "Groq API key is configured."
        )

    else:

        st.warning(
            "Enter a Groq API key before using AI features."
        )


# ============================================================
# TABS
# ============================================================

setup_tab, interview_tab, analytics_tab, report_tab = st.tabs(
    [
        "⚙️ Interview Setup",
        "🎤 Live Adaptive Interview",
        "📊 Session Analytics",
        "📄 Final Interview Report",
    ]
)


# ============================================================
# SETUP
# ============================================================

with setup_tab:

    st.markdown(
        "## ⚙️ Interview Setup"
    )

    mode = st.selectbox(
        "Interview Mode",
        INTERVIEW_MODES,
        disabled=st.session_state.started,
    )

    categories = st.multiselect(
        "Interview Categories",
        CATEGORIES,
        default=st.session_state.categories,
        disabled=st.session_state.started,
    )

    st.divider()

    duration_options = list(
        DURATIONS.keys()
    )

    duration_values = list(
        DURATIONS.values()
    )

    try:
        current_duration_index = (
            duration_values.index(
                st.session_state.session_duration
            )
        )
    except ValueError:
        current_duration_index = 0

    duration_label = st.selectbox(
        "Practice Session Duration",
        duration_options,
        index=current_duration_index,
        disabled=st.session_state.started,
    )

    duration_minutes = DURATIONS[
        duration_label
    ]

    question_mode = st.radio(
        "Question Format",
        [
            "Text Questions",
            "Audio Questions",
        ],
        index=(
            0
            if st.session_state.question_mode
            == "Text Questions"
            else 1
        ),
        disabled=st.session_state.started,
        horizontal=True,
    )

    answer_mode = st.radio(
        "Answer Format",
        [
            "⌨️ Type Answers",
            "🎙️ Speak Answers",
        ],
        index=(
            0
            if st.session_state.answer_mode
            .startswith("⌨")
            else 1
        ),
        disabled=st.session_state.started,
        horizontal=True,
    )

    use_research = st.checkbox(
        "Company / Role Web Research",
        value=False,
        disabled=st.session_state.started,
    )

    camera_enabled = st.checkbox(
        "Camera Presentation Snapshot",
        value=st.session_state.camera_enabled,
        disabled=st.session_state.started,
    )

    speech_language = st.selectbox(
        "Question Voice",
        [
            "English (US)",
            "English (UK)",
        ],
        disabled=st.session_state.started,
    )

    speech_locale = (
        "en-US"
        if speech_language == "English (US)"
        else "en-GB"
    )

    answer_length = st.selectbox(
        "AI Practice-Answer Length",
        [
            "Short",
            "Standard",
            "Detailed",
        ],
        disabled=st.session_state.started,
    )

    if not categories:
        st.warning(
            "Select at least one Interview Category."
        )

    if not st.session_state.started:

        st.session_state.session_duration = (
            duration_minutes
        )

        st.session_state.question_mode = (
            question_mode
        )

        st.session_state.answer_mode = (
            answer_mode
        )

        st.session_state.categories = (
            categories or CATEGORIES[:]
        )

        st.session_state.camera_enabled = (
            camera_enabled
        )


# ============================================================
# EVIDENCE PACK + AGENT COCKPIT
# ============================================================

left, right = st.columns(
    [1.35, 1]
)


# ============================================================
# EVIDENCE PACK
# ============================================================

with left:

    st.markdown(
        "### 1. Build the Evidence Pack"
    )

    target_role = st.text_input(
        "Target Role",
        value=st.session_state.target_role,
        placeholder="Example: AI Engineer",
        disabled=st.session_state.started,
    )

    st.session_state.target_role = (
        target_role.strip()
    )

    cv_file = st.file_uploader(
        "CV / Resume",
        type=[
            "pdf",
            "docx",
            "txt",
        ],
        key="cv",
    )

    jd_file = st.file_uploader(
        "Job Description",
        type=[
            "pdf",
            "docx",
            "txt",
        ],
        key="jd",
    )

    jd_text = st.text_area(
        "Or paste the Job Description",
        height=150,
        placeholder=(
            "Paste the JD here if you do not have a file."
        ),
    )

    company = st.text_input(
        "Company Name",
        value=st.session_state.company,
        placeholder="Optional",
        disabled=st.session_state.started,
    )

    company_track = st.text_area(
        "Optional Company-Specific Question Context",
        height=90,
        placeholder=(
            "Paste factual company interview context if available."
        ),
        disabled=st.session_state.started,
    )

    if st.button(
        "Build Evidence Pack",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.started,
    ):

        api_key = (
            st.session_state.api_key.strip()
        )

        if not api_key:

            st.error(
                "Enter a Groq API key first."
            )

        elif not target_role.strip():

            st.error(
                "Enter the target role."
            )

        elif not cv_file:

            st.error(
                "Upload a CV / Resume."
            )

        elif not (
            jd_file
            or jd_text.strip()
        ):

            st.error(
                "Upload or paste the Job Description."
            )

        else:

            try:

                st.session_state.company = (
                    company.strip()
                )

                st.session_state.company_track = (
                    company_track
                )

                cv_text = (
                    extract_uploaded_text(
                        cv_file
                    )
                )

                final_jd = (
                    extract_uploaded_text(
                        jd_file
                    )
                    if jd_file
                    else jd_text
                )

                evidence_agent = EvidenceAgent()

                st.session_state.evidence = (
                    evidence_agent.build(
                        cv_text=safe_clamp(
                            cv_text,
                            14000,
                        ),
                        jd_text=safe_clamp(
                            final_jd,
                            12000,
                        ),
                        target_role=target_role,
                        industry=(
                            "Not specified — grounded "
                            "in CV/JD and role context"
                        ),
                    )
                )

                st.session_state.research = None
                st.session_state.turns = []
                st.session_state.question = None
                st.session_state.started = False
                st.session_state.started_at = None

                if use_research:

                    try:

                        gateway = GroqGateway(
                            api_key
                        )

                        st.session_state.research = (
                            ResearchAgent(
                                gateway
                            ).run(
                                target_role,
                                (
                                    "Not specified — grounded "
                                    "in CV/JD and role context"
                                ),
                                safe_clamp(
                                    final_jd,
                                    6000,
                                ),
                                company=company,
                                company_track=company_track,
                            )
                        )

                    except Exception as exc:

                        st.warning(
                            "Research unavailable; "
                            "continuing without it. "
                            + friendly_groq_error(
                                exc
                            )
                        )

                st.success(
                    "Evidence pack created successfully."
                )

            except Exception as exc:

                st.error(
                    "Evidence pack creation failed."
                )

                st.code(
                    friendly_groq_error(exc),
                    language="text",
                )


# ============================================================
# AGENT COCKPIT
# ============================================================

with right:

    st.markdown(
        "### Agent Cockpit"
    )

    agents_status = [
        (
            "Evidence Intelligence",
            (
                "READY"
                if st.session_state.evidence
                else "WAITING"
            ),
            (
                "ready"
                if st.session_state.evidence
                else "waiting"
            ),
        ),

        (
            "Career & Market Research",
            (
                "READY"
                if st.session_state.research
                else (
                    "OPTIONAL"
                    if not use_research
                    else "WAITING"
                )
            ),
            (
                "ready"
                if st.session_state.research
                else (
                    "optional"
                    if not use_research
                    else "waiting"
                )
            ),
        ),

        (
            "Interview Strategy",
            (
                "ACTIVE"
                if st.session_state.started
                else "READY"
            ),
            (
                "active"
                if st.session_state.started
                else "ready"
            ),
        ),

        (
            "AI Interviewer",
            (
                "ACTIVE"
                if st.session_state.question
                else "READY"
            ),
            (
                "active"
                if st.session_state.question
                else "ready"
            ),
        ),

        (
            "Performance Coach",
            "READY",
            "ready",
        ),
    ]

    cockpit_html = """
    <div class="agent-cockpit">
    """

    for (
        name,
        status,
        css_class,
    ) in agents_status:

        cockpit_html += f"""
        <div class="agent">

            <span class="agent-name">
                {escape(name)}
            </span>

            <span class="status {escape(css_class)}">
                {escape(status)}
            </span>

        </div>
        """

    cockpit_html += """
        <div style="height:18px;"></div>

        <div class="cockpit-title">
            Session Design
        </div>
    """

    cockpit_html += f"""
        <b>Interview Mode</b><br>
        <span class="small">
            {escape(mode)}
        </span>

        <br><br>

        <b>Interview Categories</b><br>
        <span class="small">
            {len(categories)} selected
        </span>

        <br><br>

        <b>Duration</b><br>
        <span class="small">
            {escape(duration_label)}
        </span>

        <br><br>

        <b>Question Format</b><br>
        <span class="small">
            {escape(question_mode)}
        </span>

        <br><br>

        <b>Answer Format</b><br>
        <span class="small">
            {escape(answer_mode)}
        </span>
    """

    cockpit_html += """
    </div>
    """

    st.markdown(
        cockpit_html,
        unsafe_allow_html=True,
    )


# ============================================================
# EVIDENCE SNAPSHOT
# ============================================================

if st.session_state.evidence:

    ev = st.session_state.evidence

    st.markdown(
        "### Evidence Snapshot"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Candidate Facts",
        len(
            ev.get(
                "candidate_facts",
                [],
            )
        ),
    )

    c2.metric(
        "JD Requirements",
        len(
            ev.get(
                "jd_requirements",
                [],
            )
        ),
    )

    c3.metric(
        "Skill Gaps",
        len(
            ev.get(
                "gaps",
                [],
            )
        ),
    )

    with st.expander(
        "View Grounding Data"
    ):

        st.write(
            "**Candidate Evidence**",
            ev.get(
                "candidate_facts",
                [],
            ),
        )

        st.write(
            "**JD Requirements**",
            ev.get(
                "jd_requirements",
                [],
            ),
        )

        st.write(
            "**Matched Skills**",
            ev.get(
                "matches",
                [],
            ),
        )

        st.write(
            "**Gaps / Unknowns**",
            ev.get(
                "gaps",
                [],
            ),
        )


# ============================================================
# START INTERVIEW
# ============================================================

if (
    st.session_state.evidence
    and not st.session_state.started
):

    if st.button(
        "🚀 Start Complete Adaptive Interview",
        type="primary",
        use_container_width=True,
    ):

        api_key = (
            st.session_state.api_key.strip()
        )

        if not categories:

            st.error(
                "Select at least one interview category."
            )

        elif not api_key:

            st.error(
                "Groq API key is required."
            )

        else:

            try:

                gateway = GroqGateway(
                    api_key
                )

                strategy = StrategyAgent()

                interviewer = InterviewerAgent(
                    gateway
                )

                now = time.time()

                st.session_state.started_at = now

                (
                    _,
                    remaining,
                    _,
                ) = duration_state(
                    now,
                    duration_minutes,
                )

                target_count = question_target(
                    duration_minutes,
                    0,
                    0,
                )

                plan = strategy.plan(
                    [],
                    mode,
                    duration_label,
                    st.session_state.evidence,
                    categories=categories,
                    remaining_minutes=round(
                        remaining / 60,
                        1,
                    ),
                    target_questions=target_count,
                )

                question = (
                    interviewer.ask_question(
                        st.session_state.evidence,
                        st.session_state.research,
                        plan,
                        target_role,
                        (
                            "Not specified — grounded "
                            "in CV/JD and role context"
                        ),
                        mode,
                        company=company,
                    )
                )

                st.session_state.question = (
                    question
                )

                st.session_state.started = True

                st.session_state.session_duration = (
                    duration_minutes
                )

                st.session_state.question_mode = (
                    question_mode
                )

                st.session_state.answer_mode = (
                    answer_mode
                )

                st.session_state.categories = (
                    categories
                )

                st.session_state.company = (
                    company
                )

                st.session_state.camera_enabled = (
                    camera_enabled
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    "The adaptive interview could not generate Question 1."
                )

                st.code(
                    friendly_groq_error(exc),
                    language="text",
                )


# ============================================================
# LIVE INTERVIEW
# ============================================================

if (
    st.session_state.started
    and st.session_state.question
):

    with interview_tab:

        st.markdown(
            "### 🎤 Live Interview Studio"
        )

        (
            elapsed,
            remaining,
            expired,
        ) = duration_state(
            st.session_state.started_at,
            st.session_state.session_duration,
        )

        turn_no = (
            len(st.session_state.turns)
            + 1
        )

        target_count = question_target(
            st.session_state.session_duration,
            elapsed,
            len(st.session_state.turns),
        )

        progress = min(
            1.0,
            len(st.session_state.turns)
            / max(
                1,
                target_count,
            ),
        )

        top1, top2, top3 = st.columns(
            [1.6, 1, 1]
        )

        with top1:

            st.progress(
                progress,
                text=(
                    f"Question {turn_no} · "
                    f"adaptive target {target_count}"
                ),
            )

        with top2:

            st.metric(
                "Elapsed",
                (
                    f"{int(elapsed // 60):02d}:"
                    f"{int(elapsed % 60):02d}"
                ),
            )

        with top3:

            render_timer(
                st.session_state.started_at,
                st.session_state.session_duration,
            )

        if expired:

            st.warning(
                "Your selected practice session time has ended. "
                "Your report is ready below."
            )

            st.session_state.question = None

        else:

            if isinstance(
                st.session_state.question,
                dict,
            ):

                q_obj = (
                    st.session_state.question
                )

            else:

                q_obj = {
                    "category": "General",
                    "question": str(
                        st.session_state.question
                    ),
                }

            question_text = str(
                q_obj.get(
                    "question",
                    "",
                )
            ).strip()

            category = str(
                q_obj.get(
                    "category",
                    "General",
                )
            )

            st.markdown(
                (
                    '<span class="category">'
                    + escape(category)
                    + "</span>"
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                (
                    '<div class="question">'
                    + escape(question_text)
                    + "</div>"
                ),
                unsafe_allow_html=True,
            )

            render_speech_controls(
                question_text,
                f"question_{turn_no}",
                "Generated interview question",
                speech_locale,
                autoplay=(
                    st.session_state.question_mode
                    == "Audio Questions"
                ),
            )

            st.markdown(
                "#### Your Answer"
            )

            st.caption(
                "Answer mode locked for this session: "
                + st.session_state.answer_mode
            )

            answer = ""
            voice_transcript = ""
            audio = None

            if (
                st.session_state.answer_mode
                == "⌨️ Type Answers"
            ):

                answer = st.text_area(
                    "Type your answer",
                    key=f"answer_input_{turn_no}",
                    height=190,
                    placeholder=(
                        "Answer as if you were "
                        "in the real interview."
                    ),
                )

            else:

                audio = st.audio_input(
                    "🎙️ Record your answer",
                    sample_rate=16000,
                    key=f"answer_audio_{turn_no}",
                )

                st.caption(
                    "Speak naturally. Submit the recording when you finish."
                )

            camera = None

            if st.session_state.camera_enabled:

                camera = st.camera_input(
                    "Optional camera snapshot",
                    key=f"camera_{turn_no}",
                )

            submit = st.button(
                "Submit Answer & Get Coaching",
                type="primary",
                use_container_width=True,
            )

            if submit:

                (
                    elapsed_now,
                    _,
                    expired_now,
                ) = duration_state(
                    st.session_state.started_at,
                    st.session_state.session_duration,
                )

                if expired_now:

                    st.warning(
                        "The session time has ended."
                    )

                    st.session_state.question = None

                    st.rerun()

                elif not st.session_state.api_key:

                    st.error(
                        "Groq API key is required."
                    )

                else:

                    gateway = GroqGateway(
                        st.session_state.api_key
                    )

                    if (
                        st.session_state.answer_mode
                        == "🎙️ Speak Answers"
                        and audio is not None
                    ):

                        try:

                            voice_transcript = (
                                gateway.transcribe(
                                    audio.getvalue(),
                                    getattr(
                                        audio,
                                        "name",
                                        "answer.wav",
                                    ),
                                ).strip()
                            )

                            answer = (
                                voice_transcript
                            )

                        except Exception as exc:

                            st.error(
                                "Voice transcription failed. "
                                + friendly_groq_error(
                                    exc
                                )
                            )

                    else:

                        answer = (
                            answer or ""
                        ).strip()

                    if not answer:

                        st.error(
                            "Provide an answer before submitting."
                        )

                    else:

                        try:

                            coach = CoachAgent(
                                gateway
                            )

                            result = (
                                coach.evaluate(
                                    question=question_text,
                                    answer=answer,
                                    evidence=(
                                        st.session_state.evidence
                                    ),
                                    target_role=target_role,
                                    mode=mode,
                                    answer_length=answer_length,
                                )
                            )

                            if voice_transcript:

                                metrics = speech_metrics(
                                    answer
                                )

                            else:

                                metrics = {
                                    "words": len(
                                        answer.split()
                                    ),
                                    "filler_words": None,
                                    "estimated_seconds": None,
                                    "words_per_minute": None,
                                }

                            camera_feedback = None

                            if camera is not None:

                                try:

                                    camera_feedback = (
                                        gateway.analyze_camera(
                                            camera.getvalue(),
                                            getattr(
                                                camera,
                                                "type",
                                                "image/jpeg",
                                            ),
                                        )
                                    )

                                except Exception as exc:

                                    camera_feedback = {
                                        "available": False,
                                        "error": (
                                            friendly_groq_error(
                                                exc
                                            )
                                        ),
                                    }

                            result[
                                "speech_metrics"
                            ] = metrics

                            result[
                                "presentation_cues"
                            ] = camera_feedback

                            st.session_state.turns.append(
                                {
                                    "question": question_text,
                                    "category": category,
                                    "answer": answer,
                                    "answer_mode": (
                                        "voice"
                                        if voice_transcript
                                        else "text"
                                    ),
                                    "voice_transcript": (
                                        voice_transcript
                                    ),
                                    "feedback": result,
                                    "timestamp": (
                                        datetime.utcnow()
                                        .isoformat(
                                            timespec="seconds"
                                        )
                                    ),
                                    "elapsed_seconds": round(
                                        elapsed_now,
                                        1,
                                    ),
                                }
                            )

                            save_session(
                                st.session_state.session_id,
                                target_role,
                                (
                                    "Not specified — grounded "
                                    "in CV/JD and role context"
                                ),
                                st.session_state.turns,
                            )

                            (
                                elapsed_after,
                                remaining_after,
                                expired_after,
                            ) = duration_state(
                                st.session_state.started_at,
                                st.session_state.session_duration,
                            )

                            if expired_after:

                                st.session_state.question = None

                            else:

                                strategy = (
                                    StrategyAgent()
                                )

                                next_target = (
                                    question_target(
                                        st.session_state.session_duration,
                                        elapsed_after,
                                        len(
                                            st.session_state.turns
                                        ),
                                    )
                                )

                                plan = (
                                    strategy.plan(
                                        st.session_state.turns,
                                        mode,
                                        duration_label,
                                        st.session_state.evidence,
                                        categories=(
                                            st.session_state.categories
                                        ),
                                        remaining_minutes=round(
                                            remaining_after
                                            / 60,
                                            1,
                                        ),
                                        target_questions=(
                                            next_target
                                        ),
                                    )
                                )

                                interviewer = (
                                    InterviewerAgent(
                                        gateway
                                    )
                                )

                                st.session_state.question = (
                                    interviewer.ask_question(
                                        st.session_state.evidence,
                                        st.session_state.research,
                                        plan,
                                        target_role,
                                        (
                                            "Not specified — grounded "
                                            "in CV/JD and role context"
                                        ),
                                        mode,
                                        company=company,
                                    )
                                )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                "The answer could not be processed."
                            )

                            st.code(
                                friendly_groq_error(
                                    exc
                                ),
                                language="text",
                            )


# ============================================================
# ANALYTICS
# ============================================================

with analytics_tab:

    st.markdown(
        "### 📊 Session Analytics"
    )

    if not st.session_state.turns:

        st.info(
            "Complete at least one interview answer "
            "to see analytics."
        )

    else:

        overall_scores = []

        for turn in st.session_state.turns:

            feedback = turn.get(
                "feedback",
                {},
            )

            score = feedback.get(
                "overall",
                0,
            )

            try:

                overall_scores.append(
                    float(score)
                )

            except (
                TypeError,
                ValueError,
            ):

                pass

        average_score = (
            round(
                sum(overall_scores)
                / len(overall_scores),
                1,
            )
            if overall_scores
            else 0
        )

        a1, a2, a3 = st.columns(3)

        a1.metric(
            "Questions Completed",
            len(
                st.session_state.turns
            ),
        )

        a2.metric(
            "Average Score",
            average_score,
        )

        a3.metric(
            "Categories Covered",
            len(
                {
                    t.get(
                        "category",
                        "General",
                    )
                    for t in st.session_state.turns
                }
            ),
        )

        category_scores = defaultdict(
            list
        )

        for turn in st.session_state.turns:

            category_scores[
                turn.get(
                    "category",
                    "General",
                )
            ].append(
                turn.get(
                    "feedback",
                    {},
                ).get(
                    "overall",
                    0,
                )
            )

        st.markdown(
            "#### Category Readiness"
        )

        readiness_cols = st.columns(
            min(
                4,
                max(
                    1,
                    len(
                        category_scores
                    ),
                ),
            )
        )

        for idx, (
            category,
            values,
        ) in enumerate(
            category_scores.items()
        ):

            numeric_values = []

            for value in values:

                try:

                    numeric_values.append(
                        float(value)
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    pass

            score = (
                round(
                    sum(numeric_values)
                    / len(numeric_values)
                )
                if numeric_values
                else 0
            )

            readiness_cols[
                idx % len(readiness_cols)
            ].metric(
                category.split(" ")[0],
                score,
            )


# ============================================================
# LATEST COACHING
# ============================================================

if (
    st.session_state.started
    and st.session_state.turns
):

    latest = (
        st.session_state.turns[-1]
        .get(
            "feedback",
            {},
        )
    )

    st.markdown(
        "###
