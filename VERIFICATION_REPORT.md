# Intervia — Verification Report

Validation date: 2026-10-01

## Static validation

- Python compilation: PASS
- Existing project verifier: PASS
- Interview setup UI checks: PASS
- `Industry` removed from candidate-facing Interview Setup: PASS
- Combined tab label `Interview categories and Interview mode`: PASS
- `Text Questions` / `Audio Questions`: PASS
- `⌨️ Type Answers` / `🎙️ Speak Answers`: PASS
- Streamlit Secrets support for `GROQ_API_KEY`: PASS
- Groq model discovery/fallback gateway: PASS
- Adaptive Question 1 exception handling: PASS
- Adaptive next-question exception handling: PASS
- No API key embedded in source: PASS

## Runtime dependency target

Python 3.12 is the deployment target. Dependencies remain pinned in `requirements.txt`.

## Groq runtime limitation

Live API authentication, project/model permissions, network reachability and account-specific rate limits cannot be proven by static validation. Groq currently documents HTTP 403 for restricted models and lists GPT-OSS 120B/20B plus Llama production models as supported model IDs. The updated gateway therefore discovers visible models and falls back where possible.

## Result

The previous failure path could terminate the app because `InterviewerAgent.ask_question()` propagated a Groq exception. The updated version catches that failure at the UI boundary, displays an actionable error, and keeps the session in a safe stopped state.
