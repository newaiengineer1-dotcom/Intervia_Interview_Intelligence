import streamlit as st

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION (Must be the first Streamlit command)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="InterviewAI - Studio Cockpit",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. STATE MANAGEMENT
# -----------------------------------------------------------------------------
def init_session_state():
    """Initializes session state variables for the interview flow."""
    if 'interview_started' not in st.session_state:
        st.session_state.interview_started = False
    if 'answer_submitted' not in st.session_state:
        st.session_state.answer_submitted = False
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = 'voice'

# -----------------------------------------------------------------------------
# 3. CUSTOM CSS (ULTRA PREMIUM THEME)
# -----------------------------------------------------------------------------
def load_css():
    """Injects the custom CSS for the dark, premium dashboard theme."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        .stApp {
            background-color: #0E1117;
            color: #E2E8F0;
        }
        
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #12151C !important;
            border-right: 1px solid #1F2937;
            padding-top: 20px;
        }
        
        /* Custom Card Classes */
        .css-card {
            background-color: #171A22;
            border: 1px solid #2D313A;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        }
        
        .css-card-prompt {
            background: linear-gradient(145deg, #1A1D24, #14171E);
            border: 1px solid #3B4252;
            border-left: 4px solid #8B5CF6;
        }
        
        /* Typography & Badges */
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: inline-block;
            margin-right: 5px;
        }
        
        .badge-purple { background-color: rgba(139, 92, 246, 0.2); color: #A78BFA; border: 1px solid #8B5CF6; }
        .badge-red { background-color: rgba(239, 68, 68, 0.2); color: #F87171; border: 1px solid #EF4444; }
        .badge-green { background-color: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #10B981; }
        .badge-blue { background-color: rgba(59, 130, 246, 0.2); color: #60A5FA; border: 1px solid #3B82F6; }
        .badge-gray { background-color: #2D3748; color: #A0AEC0; border: 1px solid #4A5568; }
        
        .text-accent-cyan { color: #22D3EE; }
        .text-accent-purple { color: #A78BFA; }
        .text-muted { color: #64748B; }
        
        /* Navigation Tabs */
        .nav-tab {
            padding: 8px 16px;
            border-radius: 8px;
            background-color: transparent;
            color: #94A3B8;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            margin-right: 8px;
            border: 1px solid transparent;
            display: inline-block;
        }
        .nav-tab.active {
            background-color: #2D3748;
            color: #FFFFFF;
            border: 1px solid #4A5568;
        }
        
        /* Progress Bar */
        .progress-container {
            width: 100%;
            background-color: #2D3748;
            border-radius: 4px;
            height: 6px;
            margin-top: 8px;
            display: flex;
            gap: 4px;
        }
        .progress-segment {
            flex: 1;
            height: 100%;
            border-radius: 4px;
            background-color: #2D3748;
        }
        .progress-segment.filled { background-color: #22D3EE; }
        .progress-segment.active { background-color: #3B82F6; }

        /* Waveform Animation */
        .waveform {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            height: 60px;
            margin: 20px 0;
        }
        .wave-bar {
            width: 4px;
            background-color: #A78BFA;
            border-radius: 2px;
            animation: pulse 1.5s infinite ease-in-out;
        }
        @keyframes pulse {
            0%, 100% { transform: scaleY(0.5); opacity: 0.5; }
            50% { transform: scaleY(1); opacity: 1; }
        }
        
        /* Native Streamlit Button Overrides */
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            border: 1px solid #4A5568;
            background-color: #1A202C;
            color: #E2E8F0;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            border-color: #8B5CF6;
            color: #FFFFFF;
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.3);
        }
        
        /* Target Streamlit's Primary Button */
        .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #6366F1, #A855F7) !important;
            border: none !important;
            color: white !important;
        }
        .stButton > button[kind="primary"]:hover {
            box-shadow: 0 0 15px rgba(168, 85, 247, 0.5) !important;
        }
        
        /* Text Area Styling */
        .stTextArea textarea {
            background-color: #12151C !important;
            color: #E2E8F0 !important;
            border: 1px solid #2D313A !important;
            border-radius: 8px !important;
        }
        .stTextArea textarea:focus {
            border-color: #8B5CF6 !important;
            box-shadow: 0 0 0 1px #8B5CF6 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. UI COMPONENTS (Reusable Functions)
# -----------------------------------------------------------------------------
def render_badge(text, badge_type="gray"):
    """Helper to render a styled badge."""
    return f"<span class='badge badge-{badge_type}'>{text}</span>"

def render_sidebar():
    """Renders the left sidebar with candidate profile and context."""
    with st.sidebar:
        st.markdown("""
        <div style='display:flex; align-items:center; margin-bottom:20px;'>
            <div style='background: linear-gradient(135deg, #6366F1, #A855F7); border-radius: 8px; width: 32px; height: 32px; display:flex; justify-content:center; align-items:center; margin-right:10px;'>
                <span style='color:white; font-weight:bold;'>AI</span>
            </div>
            <div>
                <h3 style='margin:0; font-size:16px;'>InterviewAI</h3>
                <p style='margin:0; font-size:10px; color:#64748B; letter-spacing:1px;'>STUDIO COCKPIT</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<p style='font-size:11px; font-weight:600; color:#64748B; margin-bottom:5px;'>TARGET PROFILE</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:14px; margin:0;'>Backend Software Eng</p>", unsafe_allow_html=True)
        st.markdown(render_badge("Mid-Level", "blue") + render_badge("Tier 1 Target", "gray"), unsafe_allow_html=True)
        
        st.markdown("<hr style='border-color: #1F2937; margin: 15px 0;'>", unsafe_allow_html=True)
        
        st.markdown("<p style='font-size:11px; font-weight:600; color:#64748B; margin-bottom:5px;'>PERSONA MODEL</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(render_badge("FAANG-Style", "purple"), unsafe_allow_html=True)
            st.markdown(render_badge("Strict Exec", "gray"), unsafe_allow_html=True)
        with col2:
            st.markdown(render_badge("Friendly", "gray"), unsafe_allow_html=True)
            st.markdown(render_badge("Startup CTO", "gray"), unsafe_allow_html=True)
            
        st.markdown("<hr style='border-color: #1F2937; margin: 15px 0;'>", unsafe_allow_html=True)
        
        st.markdown("<p style='font-size:11px; font-weight:600; color:#64748B; margin-bottom:5px;'>EVALUATION VECTOR</p>", unsafe_allow_html=True)
        st.markdown(render_badge("Technical", "purple") + render_badge("STAR Behavioral", "gray"), unsafe_allow_html=True)
        st.markdown(render_badge("System Design", "gray") + render_badge("Live Coding", "gray"), unsafe_allow_html=True)
        
        st.markdown("<hr style='border-color: #1F2937; margin: 15px 0;'>", unsafe_allow_html=True)
        
        # Adaptive Escalation Progress
        st.markdown("""
        <div style='display:flex; justify-content:space-between; font-size:11px; color:#64748B; font-weight:600;'>
            <span>ADAPTIVE ESCALATION</span>
            <span class='text-accent-cyan'>Hard L5</span>
        </div>
        <div style='background:#2D3748; border-radius:4px; height:4px; margin-top:5px;'>
            <div style='background:#22D3EE; width:70%; height:100%; border-radius:4px;'></div>
        </div>
        <div style='display:flex; justify-content:space-between; font-size:10px; color:#64748B; margin-top:5px;'>
            <span>L3 Core</span>
            <span>L6 Architect</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<hr style='border-color: #1F2937; margin: 15px 0;'>", unsafe_allow_html=True)
        
        st.markdown("<p style='font-size:11px; font-weight:600; color:#64748B; margin-bottom:5px;'>CONTEXT INGESTION</p>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background:#1A1D24; padding:8px; border-radius:6px; border:1px solid #2D313A; font-size:12px; margin-bottom:5px;'>
            <span style='color:#10B981;'>✔</span> Resume: 4 Projects, 12 Skills
        </div>
        <div style='background:#1A1D24; padding:8px; border-radius:6px; border:1px solid #2D313A; font-size:12px;'>
            <span style='color:#10B981;'>✔</span> JD: 6 Critical Competencies
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Primary Action Button
        if st.button("🚀 Start Interview", type="primary", use_container_width=True):
            st.session_state.interview_started = True
            st.toast("Interview Initialized! Good luck.", icon="🚀")

def render_top_header():
    """Renders the top navigation breadcrumbs and tabs."""
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; font-size:12px; color:#94A3B8;'>
        <div>
            <span>Workspace</span> <span style='color:#4A5568;'>›</span> 
            <span>Session telemetry #sess-8f3a</span> 
            <span style='background:#2D3748; padding:2px 8px; border-radius:4px; margin-left:10px;'>Model: FAANG-Style</span>
            <span class='badge badge-red' style='margin-left:10px;'>Hard (Escalated)</span>
            <span class='badge badge-purple' style='margin-left:5px;'>Stripe / Tier 1 Backend</span>
        </div>
        <div style='font-size:16px;'>🔊 &nbsp; 🕒 &nbsp; ⬇️ &nbsp; 👤</div>
    </div>
    """, unsafe_allow_html=True)

    # Primary Nav
    tabs = ["Live Adaptive Interview", "6-D Evaluation", "JD → Curriculum", "Resume & ATS Gap", "Live Coding", "Executive Performance"]
    tab_html = "<div style='margin-bottom: 20px;'>"
    for t in tabs:
        active = "active" if t == "Live Adaptive Interview" else ""
        tab_html += f"<span class='nav-tab {active}'>{t}</span>"
    tab_html += "</div>"
    st.markdown(tab_html, unsafe_allow_html=True)

    # Secondary Sub-Nav
    sub_tabs = ["🎤 1. Live Adaptive Interview", "⚖️ 2. 6-D Evaluation", "⚙️ 3. JD → Curriculum", "📄 4. Resume & ATS Gap", "💻 5. Live Coding IDE"]
    sub_html = "<div style='margin-bottom: 25px; background: #12151C; padding: 10px; border-radius: 8px; border: 1px solid #1F2937;'>"
    for i, t in enumerate(sub_tabs):
        active = "active" if i == 0 else ""
        sub_html += f"<span class='nav-tab {active}'>{t}</span>"
    sub_html += "</div>"
    st.markdown(sub_html, unsafe_allow_html=True)

def render_question_progress():
    """Renders the question progress bar and difficulty badge."""
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:20px;'>
        <div style='display:flex; align-items:center; gap:20px;'>
            <div>
                <h2 style='margin:0; font-size:24px;'>Question 3 <span style='color:#64748B; font-weight:400;'>of 6</span></h2>
                <p style='margin:0; font-size:12px; color:#94A3B8;'>Backend / Infrastructure</p>
            </div>
            <div class='progress-container' style='width:200px;'>
                <div class='progress-segment filled'></div>
                <div class='progress-segment filled'></div>
                <div class='progress-segment active'></div>
                <div class='progress-segment'></div>
                <div class='progress-segment'></div>
                <div class='progress-segment'></div>
            </div>
        </div>
        <div style='text-align:right;'>
            <span class='badge badge-red'>⚡ Hard (Escalated from Medium)</span>
            <div style='font-size:12px; color:#94A3B8; margin-top:5px;'>
                <span style='color:#22D3EE;'>Candidate L5</span> • Benchmark: Stripe Eng II
            </div>
            <div style='font-size:12px; color:#94A3B8; margin-top:5px;'>
                🕒 14:32 remaining
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. MAIN EXECUTION BLOCK
# -----------------------------------------------------------------------------
def main():
    init_session_state()
    load_css()
    render_sidebar()
    render_top_header()
    render_question_progress()

    col_left, col_right = st.columns([1.1, 1], gap="large")

    # --- LEFT COLUMN ---
    with col_left:
        # AI Interviewer Profile
        st.markdown("""
        <div class='css-card' style='display:flex; justify-content:space-between; align-items:center;'>
            <div style='display:flex; align-items:center; gap:15px;'>
                <div style='background: linear-gradient(135deg, #22D3EE, #6366F1); border-radius: 50%; width: 48px; height: 48px; display:flex; justify-content:center; align-items:center;'>
                    <span style='font-size:24px;'>🤖</span>
                </div>
                <div>
                    <h4 style='margin:0; font-size:16px;'>Aria-6X <span style='color:#22D3EE; font-size:14px;'>✦</span></h4>
                    <p style='margin:0; font-size:12px; color:#94A3B8;'>FAANG-Style • Principal Engineer Tier</p>
                </div>
            </div>
            <div style='text-align:right;'>
                <span class='badge badge-gray'>ACTIVE PROBE</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Prompt Card
        st.markdown("""
        <div class='css-card css-card-prompt'>
            <p style='font-size:11px; font-weight:700; color:#A78BFA; margin-bottom:10px; letter-spacing:1px;'>📝 TECHNICAL ESCALATION PROMPT</p>
            <p style='font-size:15px; line-height:1.6; margin:0; color:#E2E8F0;'>
                "You mentioned deploying Django applications with Docker. Walk me through how you containerized the application, managed multi-stage builds, and handled production configuration & secrets without baking them into image layers."
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Active Evaluation Focus
        st.markdown("<p style='font-size:11px; font-weight:700; color:#64748B; margin-bottom:8px;'>ACTIVE EVALUATION FOCUS</p>", unsafe_allow_html=True)
        st.markdown("""
        <div style='margin-bottom:20px;'>
            <span class='badge badge-gray' style='border-color:#8B5CF6; color:#A78BFA;'>Multi-Stage Artifacts</span>
            <span class='badge badge-gray' style='border-color:#8B5CF6; color:#A78BFA;'>BuildKit Secrets</span>
            <span class='badge badge-gray' style='border-color:#8B5CF6; color:#A78BFA;'>Non-root Daemon UID</span>
            <span class='badge badge-gray' style='border-color:#8B5CF6; color:#A78BFA;'>Alpine vs Slim Glibc</span>
        </div>
        """, unsafe_allow_html=True)

        # User Status
        st.markdown("""
        <div style='display:flex; justify-content:space-between; align-items:center; background:#12151C; padding:10px 15px; border-radius:8px; border:1px solid #1F2937; margin-bottom:20px;'>
            <div style='display:flex; align-items:center; gap:10px;'>
                <div style='background:#2D3748; border-radius:50%; width:24px; height:24px; display:flex; justify-content:center; align-items:center; font-size:12px;'>👤</div>
                <span style='font-size:13px;'>Alex Chen (You)</span>
            </div>
            <div style='font-size:12px; color:#10B981;'>Mic Connected • Latency 18ms</div>
        </div>
        """, unsafe_allow_html=True)

        # Architect Tip
        st.markdown("""
        <div style='background: rgba(34, 211, 238, 0.05); border-left: 3px solid #22D3EE; padding: 15px; border-radius: 0 8px 8px 0;'>
            <p style='margin:0; font-size:12px; font-weight:700; color:#22D3EE;'>💡 Senior Architect Tip</p>
            <p style='margin:5px 0 0 0; font-size:13px; color:#94A3B8; line-height:1.5;'>
                Address build cache invalidation order and how you mitigate running Python processes as root in standard ECS/EKS worker pools.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # --- RIGHT COLUMN ---
    with col_right:
        # Mode Toggle
        mode_col1, mode_col2 = st.columns([2, 1])
        with mode_col1:
            mode = st.radio("Mode", ["🎤 Voice Stream Active", "⌨️ Text Mode"], 
                            horizontal=True, label_visibility="collapsed")
            st.session_state.app_mode = 'voice' if "Voice" in mode else 'text'
        with mode_col2:
            st.markdown("<div style='text-align:right; font-size:11px; color:#10B981; font-weight:600; padding-top:10px;'>WHISPER-V3 ONLINE ●</div>", unsafe_allow_html=True)

        # Conditional Rendering based on Mode
        if st.session_state.app_mode == 'voice':
            # Audio Buffer Card
            st.markdown("""
            <div class='css-card' style='text-align:center; padding:30px 20px;'>
                <p style='font-size:11px; font-weight:700; color:#64748B; letter-spacing:1px; margin-bottom:5px;'>LIVE NEURAL AUDIO BUFFER</p>
                <h1 style='font-size:36px; margin:0; font-weight:700;'>01:24</h1>
                
                <div class='waveform'>
                    <div class='wave-bar' style='height: 20px; animation-delay: 0.1s;'></div>
                    <div class='wave-bar' style='height: 40px; animation-delay: 0.2s;'></div>
                    <div class='wave-bar' style='height: 30px; animation-delay: 0.3s;'></div>
                    <div class='wave-bar' style='height: 50px; animation-delay: 0.4s;'></div>
                    <div class='wave-bar' style='height: 25px; animation-delay: 0.5s;'></div>
                    <div class='wave-bar' style='height: 60px; animation-delay: 0.6s; background-color:#22D3EE;'></div>
                    <div class='wave-bar' style='height: 35px; animation-delay: 0.7s;'></div>
                    <div class='wave-bar' style='height: 45px; animation-delay: 0.8s;'></div>
                    <div class='wave-bar' style='height: 20px; animation-delay: 0.9s;'></div>
                    <div class='wave-bar' style='height: 55px; animation-delay: 1.0s; background-color:#22D3EE;'></div>
                </div>
                
                <div style='background: linear-gradient(135deg, #A855F7, #6366F1); border-radius: 50%; width: 64px; height: 64px; display:flex; justify-content:center; align-items:center; margin: 0 auto 15px auto; box-shadow: 0 0 20px rgba(168, 85, 247, 0.4); cursor:pointer;'>
                    <span style='font-size:28px;'>🎤</span>
                </div>
                <p style='font-size:13px; color:#94A3B8; margin:0;'>Recording in progress... Click to pause</p>
            </div>
            """, unsafe_allow_html=True)

            # Audio Metrics Grid
            st.markdown("""
            <div style='display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; margin-bottom:20px;'>
                <div style='background:#12151C; border:1px solid #1F2937; border-radius:8px; padding:10px; text-align:center;'>
                    <p style='font-size:10px; color:#64748B; margin:0 0 5px 0; font-weight:600;'>SPEAKING PACE</p>
                    <p style='font-size:16px; color:#22D3EE; margin:0; font-weight:700;'>142 <span style='font-size:10px; color:#64748B; font-weight:400;'>WPM</span></p>
                    <p style='font-size:10px; color:#10B981; margin:2px 0 0 0;'>Optimal ●</p>
                </div>
                <div style='background:#12151C; border:1px solid #1F2937; border-radius:8px; padding:10px; text-align:center;'>
                    <p style='font-size:10px; color:#64748B; margin:0 0 5px 0; font-weight:600;'>FILLER WORDS</p>
                    <p style='font-size:16px; color:#FBBF24; margin:0; font-weight:700;'>2 <span style='font-size:10px; color:#64748B; font-weight:400;'>detected</span></p>
                    <p style='font-size:10px; color:#94A3B8; margin:2px 0 0 0;'>um, like ●</p>
                </div>
                <div style='background:#12151C; border:1px solid #1F2937; border-radius:8px; padding:10px; text-align:center;'>
                    <p style='font-size:10px; color:#64748B; margin:0 0 5px 0; font-weight:600;'>DURATION</p>
                    <p style='font-size:16px; color:#E2E8F0; margin:0; font-weight:700;'>1m 24s</p>
                    <p style='font-size:10px; color:#64748B; margin:2px 0 0 0;'>Max 3m 00s</p>
                </div>
                <div style='background:#12151C; border:1px solid #1F2937; border-radius:8px; padding:10px; text-align:center;'>
                    <p style='font-size:10px; color:#64748B; margin:0 0 5px 0; font-weight:600;'>CLARITY SCORE</p>
                    <p style='font-size:16px; color:#10B981; margin:0; font-weight:700;'>9.2<span style='font-size:10px; color:#64748B; font-weight:400;'>/10</span></p>
                    <p style='font-size:10px; color:#10B981; margin:2px 0 0 0;'>Enunciation ●</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Text Mode Input
            st.markdown("<div class='css-card'>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:12px; font-weight:600; color:#E2E8F0; margin-bottom:10px;'>⌨️ Type Your Response</p>", unsafe_allow_html=True)
            st.text_area("Type your answer here...", height=250, label_visibility="collapsed", key="text_mode_input")
            st.markdown("</div>", unsafe_allow_html=True)

        # Transcription Area (Common to both modes, acts as output buffer)
        st.markdown("""
        <div class='css-card' style='padding:15px 15px 5px 15px; margin-top:20px;'>
            <div style='display:flex; justify-content:space-between; margin-bottom:10px;'>
                <span style='font-size:12px; font-weight:600; color:#E2E8F0;'>📝 Live Real-Time Transcription / Buffer</span>
                <span style='font-size:11px; color:#64748B;'>Click text below to edit prior to calibration</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        transcript_default = "So for our container pipeline, um we started with a multi-stage Alpine Dockerfile. In the build stage, we compiled wheels, and in the runtime stage, we copied only wheels... like avoiding gcc bloat. We also passed environment secrets via AWS Secrets Manager at task startup so they were not baked into layers."
        st.text_area("Transcript", value=transcript_default, height=120, label_visibility="collapsed")

        # Action Buttons
        st.markdown("<br>", unsafe_allow_html=True)
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1.5])
        with btn_col1:
            if st.button("🔄 Re-record & Reset", use_container_width=True):
                st.toast("Recording reset.", icon="🔄")
        with btn_col2:
            if st.button("✨ Auto-Remove Fillers", use_container_width=True):
                st.toast("Fillers removed from transcript.", icon="✨")
        with btn_col3:
            if st.button("Submit Answer & Calibrate 🚀", type="primary", use_container_width=True):
                with st.spinner("Calibrating response against FAANG benchmarks..."):
                    # Simulate processing time
                    import time
                    time.sleep(1.5)
                st.success("Answer submitted successfully! Calibrating...")
                st.balloons()

if __name__ == "__main__":
    main()
