# Intervia — Interview Intelligence

Evidence-Grounded Adaptive Interview Intelligence for realistic interview practice.

## What this version adds
- **Interview Setup** now combines **Interview categories and Interview mode** in one professional tab.
- In Audio Questions mode, the generated question is displayed and browser speech automatically reads it when autoplay is permitted; playback stops when the utterance ends.
- Choose **Text Questions / Audio Questions** and **⌨️ Type Answers / 🎙️ Speak Answers** once for the whole session.
- Speak Answers uses Groq Whisper Large V3 Turbo for transcription.
- Choose **30, 60, 120 or 180 Minutes**.
- Question pacing automatically adjusts to elapsed time, completed turns and answer speed.
- Seven core interview categories are supported.
- Optional company-specific context and web research. The visible **Industry** field has been removed; grounding is driven by the CV, JD, target role, categories, mode and optional company context.
- Optional camera snapshot presentation-cue feedback.
- Category readiness dashboard and PDF/Markdown reports.
- Five-agent architecture remains: Evidence, Research, Strategy, Interviewer, Coach. Evidence/Strategy are mostly deterministic; Interviewer/Coach are the primary LLM agents.

## Seven categories
1. Behavioral & Situational 🎭
2. Technical & Role-Specific 💻
3. HR & Screening Basics 🤝
4. Leadership & Management 👔
5. Case & Analytical Interviews 📊
6. Competency & Skill-Based 🧠
7. Reverse Interviewing — Questions for the Employer 🔍

## Voice notes
Question playback is browser-native and does not require a separate paid TTS API. Candidate voice answers are transcribed with Groq Whisper Large V3 Turbo.

## Camera notes
The Streamlit MVP uses a camera snapshot, not continuous video. It reports observable presentation cues only. Real-time body-language analytics requires a dedicated video/WebRTC pipeline and is documented as a production upgrade.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

Keep API keys in Streamlit Secrets for deployment. Do not commit credentials to GitHub.
