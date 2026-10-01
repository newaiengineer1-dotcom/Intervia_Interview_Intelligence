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

## Adaptive interview Groq troubleshooting (2026-10-01 update)

The adaptive interviewer now discovers models visible to the current Groq project/key and tries them in this order when available:
1. `openai/gpt-oss-120b`
2. `openai/gpt-oss-20b`
3. `llama-3.3-70b-versatile`
4. `llama-3.1-8b-instant`

This prevents the interview from crashing simply because the preferred model is restricted. If all accessible models fail, the UI shows the actual Groq error instead of a redacted Streamlit traceback.

### If the UI reports HTTP 403
A 403 from Groq can mean that the selected model is blocked at the organization or project level. In Groq Console, check **Settings → Organization → Limits** and **Project → Limits**, and allow at least one model from the fallback list. Groq documents that restricted models return HTTP 403.

### If the UI reports HTTP 401
Replace the key with an active Groq API key. On Streamlit Community Cloud, put it in **App → Settings → Secrets**:

```toml
GROQ_API_KEY = "gsk_..."
```

The application reads Streamlit Secrets first and environment variables second. Never commit the key to GitHub.

### If the UI reports HTTP 429
This is a quota/rate-limit condition, not a Python syntax problem. Use a shorter session, concise answers, wait for the quota window, or use a project with higher limits.

### Important
The code cannot bypass a Groq organization/project permission block, invalid API key, external network block, or exhausted quota. The updated app now reports these conditions directly and keeps the Streamlit session alive instead of crashing at Question 1.
