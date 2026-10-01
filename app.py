```python
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
# INTERVIEW SETUP
# ============================================================

with setup_tab:

    st.markdown("## ⚙️ Interview Setup")
    st.caption(
        "Configure the primary interview style and the specific categories "
        "you want Intervia to cover."
    )

    # --------------------------------------------------------
    # INTERVIEW MODE
    # --------------------------------------------------------

    mode = st.selectbox(
        "Interview Mode",
        [
            "Mixed",
            "Technical",
            "Behavioral",
            "Case / Situational",
            "HR / Screening",
            "Leadership",
        ],
        disabled=st.session_state.started,
        help=(
            "Select the primary style of interview. "
            "The AI interviewer uses this as the main questioning direction."
        ),
    )

    # --------------------------------------------------------
    # INTERVIEW CATEGORIES
    # --------------------------------------------------------

    categories = st.multiselect(
        "Interview Categories",
        [
            "Behavioral & Situational 🎭",
            "Technical & Role-Specific 💻",
            "HR & Screening Basics 🤝",
            "Leadership & Management 👔",
            "Case & Analytical Interviews 📊",
            "Competency & Skill-Based 🧠",
            "Reverse Interviewing — Questions for the Employer 🔍",
        ],
        default=st.session_state.categories,
        disabled=st.session_state.started,
        help=(
            "Select one or more categories. "
            "The adaptive strategy agent balances these categories "
            "throughout the interview."
        ),
    )

    st.divider()

    # --------------------------------------------------------
    # SESSION DURATION
    # --------------------------------------------------------

    duration_label = st.selectbox(
        "Practice Session Duration",
        list(DURATIONS.keys()),
        index=(
            0
            if st.session_state.session_duration == 30
            else list(DURATIONS.values()).index(
                st.session_state.session_duration
            )
        ),
        disabled=st.session_state.started,
    )

    duration_minutes = DURATIONS[duration_label]

    # --------------------------------------------------------
    # QUESTION FORMAT
    # --------------------------------------------------------

    question_mode = st.radio(
        "Question Format",
        ["Text Questions", "Audio Questions"],
        index=(
            0
            if st.session_state.question_mode == "Text Questions"
            else 1
        ),
        disabled=st.session_state.started,
        horizontal=True,
        help=(
            "Text Questions displays the question on screen. "
            "Audio Questions also reads the question aloud."
        ),
    )

    # --------------------------------------------------------
    # ANSWER FORMAT
    # --------------------------------------------------------

    answer_mode = st.radio(
        "Answer Format",
        ["⌨️ Type Answers", "🎙️ Speak Answers"],
        index=(
            0
            if st.session_state.answer_mode.startswith("⌨")
            else 1
        ),
        disabled=st.session_state.started,
        horizontal=True,
        help=(
            "Type Answers uses a text box. "
            "Speak Answers records your response and sends it "
            "to Groq Whisper for transcription."
        ),
    )

    # --------------------------------------------------------
    # OPTIONAL RESEARCH
    # --------------------------------------------------------

    use_research = st.checkbox(
        "Company / Role Web Research",
        value=False,
        disabled=st.session_state.started,
        help=(
            "Optionally research the company and role context "
            "before starting the interview."
        ),
    )

    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    camera_enabled = st.checkbox(
        "Camera Presentation Snapshot",
        value=st.session_state.camera_enabled,
        disabled=st.session_state.started,
        help=(
            "Optional snapshot analysis of observable "
            "presentation/framing cues."
        ),
    )

    # --------------------------------------------------------
    # QUESTION VOICE
    # --------------------------------------------------------

    speech_language = st.selectbox(
        "Question Voice",
        ["English (US)", "English (UK)"],
        index=0,
        disabled=st.session_state.started,
    )

    speech_locale = (
        "en-US"
        if speech_language == "English (US)"
        else "en-GB"
    )

    # --------------------------------------------------------
    # AI ANSWER LENGTH
    # --------------------------------------------------------

    answer_length = st.selectbox(
        "AI Practice-Answer Length",
        ["Short", "Standard", "Detailed"],
        disabled=st.session_state.started,
    )

    st.divider()

    st.caption(
        "💡 Choose the interview mode and categories once. "
        "Intervia will keep them fixed throughout the session."
    )

    st.caption(
        "🔐 Production: keep your Groq API key in Streamlit Secrets "
        "instead of committing it to GitHub."
    )

    # --------------------------------------------------------
    # SAVE SETTINGS
    # --------------------------------------------------------

    if not st.session_state.started:

        st.session_state.session_duration = duration_minutes

        st.session_state.question_mode = question_mode

        st.session_state.answer_mode = answer_mode

        st.session_state.categories = (
            categories
            if categories
            else [
                "Behavioral & Situational 🎭",
                "Technical & Role-Specific 💻",
                "HR & Screening Basics 🤝",
                "Leadership & Management 👔",
                "Case & Analytical Interviews 📊",
                "Competency & Skill-Based 🧠",
                "Reverse Interviewing — Questions for the Employer 🔍",
            ]
        )

        st.session_state.company = ""

        st.session_state.company_track = ""

        st.session_state.camera_enabled = camera_enabled
```

### The UI will now be

**Interview Mode**

`Mixed`
`Technical`
`Behavioral`
`Case / Situational`
`HR / Screening`
`Leadership`

**Interview Categories**

☑ Behavioral & Situational 🎭
☑ Technical & Role-Specific 💻
☑ HR & Screening Basics 🤝
☑ Leadership & Management 👔
☑ Case & Analytical Interviews 📊
☑ Competency & Skill-Based 🧠
☑ Reverse Interviewing — Questions for the Employer 🔍

The user can select **one Interview Mode** and **multiple Interview Categories**.

**Important:** Replace the old `# TABS` through the end of the old setup section with the block above. Do **not** keep the old nested `with setup_tab:` block, otherwise you can still get duplicate UI elements.
