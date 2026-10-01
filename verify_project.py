from pathlib import Path
import py_compile

ROOT = Path(__file__).parent
for name in ["app.py", "agents.py", "rag.py", "db.py", "report.py", "utils.py", "crew_adapter.py"]:
    py_compile.compile(str(ROOT / name), doraise=True)

app = (ROOT / "app.py").read_text(encoding="utf-8")
checks = {
    "question_audio_controls": "render_speech_controls(" in app and "Audio Questions" in app,
    "text_answer_mode": "⌨️ Type Answers" in app,
    "voice_answer_mode": "🎙️ Speak Answers" in app,
    "whisper_transcription": "gateway.transcribe" in app,
    "seven_categories": "Behavioral & Situational 🎭" in app and "Reverse Interviewing" in app,
    "combined_setup_tab": "Interview categories and Interview mode" in app and "setup_tab, = st.tabs" in app,
    "industry_removed_from_ui": 'st.text_input("Industry"' not in app and 'Industry' not in app.split('with st.sidebar:', 1)[1].split('st.markdown(', 1)[0],
    "four_durations": all(x in app for x in ["30 Minutes", "60 Minutes", "120 Minutes", "180 Minutes"]),
    "auto_question_audio": 'autoplay=(st.session_state.question_mode == "Audio Questions")' in app,
    "adaptive_target": "question_target" in app,
    "transcript_playback": "voice_transcript" in app and "Speech analytics" in app,
    "interviewer_ui_alias": "def ask_question(" in (ROOT / "agents.py").read_text(encoding="utf-8"),
}
failed = [k for k, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Failed checks: " + ", ".join(failed))
print("PASS: Python compilation and voice-interview UI checks")
