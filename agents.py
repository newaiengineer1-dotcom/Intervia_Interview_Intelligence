import json
import re
from typing import Any

from utils import average_scores, safe_clamp

PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "openai/gpt-oss-20b"
WHISPER_MODEL = "whisper-large-v3-turbo"


def _json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise


class GroqGateway:
    def __init__(self, api_key: str):
        try:
            from groq import Groq
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt before using Groq features.") from exc
        self.client = Groq(api_key=api_key)

    def chat_json(self, system: str, user: str, max_tokens: int = 900) -> dict:
        prompt = safe_clamp(user, 15000)
        last_exc = None
        for model in (PRIMARY_MODEL, FALLBACK_MODEL):
            try:
                resp = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                    temperature=0.25,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                return _json(resp.choices[0].message.content)
            except Exception as exc:
                last_exc = exc
        raise RuntimeError(f"Groq request failed on primary and fallback models: {last_exc}")

    def chat_text(self, system: str, user: str, max_tokens: int = 250) -> str:
        last_exc = None
        for model in (PRIMARY_MODEL, FALLBACK_MODEL):
            try:
                resp = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": safe_clamp(user, 10000)}],
                    temperature=0.35,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content.strip()
            except Exception as exc:
                last_exc = exc
        raise RuntimeError(f"Groq request failed: {last_exc}")

    def transcribe(self, data: bytes, filename: str) -> str:
        result = self.client.audio.transcriptions.create(
            file=(filename or "answer.wav", data),
            model=WHISPER_MODEL,
            response_format="text",
        )
        return result if isinstance(result, str) else getattr(result, "text", str(result))

    def analyze_camera(self, data: bytes, mime_type: str = "image/jpeg") -> dict[str, Any]:
        # The MVP intentionally avoids inferring emotions, personality, health or other
        # sensitive traits from camera images. Return a truthful capture status instead
        # of making a second model call solely for presentation analysis.
        return {
            "available": False,
            "captured": bool(data),
            "mime_type": mime_type,
            "message": "Camera snapshot captured. Automated visual/personality inference is disabled in this lightweight MVP.",
        }


class EvidenceAgent:
    """Deterministic agent: never turns JD requirements into candidate facts."""

    STOP = {
        "and", "the", "with", "for", "from", "this", "that", "have", "will", "your", "you",
        "are", "our", "their", "into", "using", "years", "role", "work", "team", "job", "about",
    }

    def _sentences(self, text: str) -> list[str]:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) > 20]

    def _terms(self, text: str) -> set[str]:
        return {x.lower() for x in re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{2,}", text) if x.lower() not in self.STOP}

    def build(self, cv_text: str, jd_text: str, target_role: str, industry: str) -> dict[str, Any]:
        cv_sentences = self._sentences(cv_text)
        jd_sentences = self._sentences(jd_text)
        cv_terms = self._terms(cv_text)
        jd_terms = self._terms(jd_text)
        shared = sorted(cv_terms & jd_terms)
        gaps = sorted(jd_terms - cv_terms)
        return {
            "target_role": target_role,
            "industry": industry,
            "candidate_facts": cv_sentences[:80],
            "jd_requirements": jd_sentences[:80],
            "candidate_terms": sorted(cv_terms)[:250],
            "jd_terms": sorted(jd_terms)[:250],
            "matches": shared[:80],
            "gaps": gaps[:80],
            "grounding_rule": "Candidate facts come only from CV. JD requirements and external research are never candidate facts.",
        }


class ResearchAgent:
    def __init__(self, gateway: GroqGateway):
        self.gateway = gateway

    def run(self, target_role: str, industry: str, jd: str, company: str = "", company_track: str = "") -> dict[str, Any]:
        try:
            response = self.gateway.client.chat.completions.create(
                model=FALLBACK_MODEL,
                messages=[
                    {"role": "system", "content": "Research only. Return concise public context. Never claim the candidate has any researched skill or experience."},
                    {"role": "user", "content": f"Role: {target_role}\nIndustry: {industry}\nCompany: {company or "Not specified"}\nCompany-specific track context: {safe_clamp(company_track, 1800)}\nJD:\n{safe_clamp(jd, 5000)}\nFind useful current role/company/industry context."},
                ],
                tools=[{"type": "browser_search"}],
                tool_choice="required",
                max_tokens=700,
            )
            msg = response.choices[0].message
            return {"available": True, "summary": msg.content or "Research completed.", "source_class": "external"}
        except Exception as exc:
            return {"available": False, "summary": "Research unavailable.", "error": str(exc), "source_class": "external"}


class StrategyAgent:
    """Deterministic adaptive policy; no LLM required."""

    def plan(self, turns: list[dict], mode: str, duration: str, evidence: dict, categories: list[str] | None = None, remaining_minutes: float | None = None, target_questions: int | None = None) -> dict[str, Any]:
        scores = []
        for t in turns:
            if t.get("feedback"):
                scores.append(t["feedback"].get("scores", {}))
        avg = average_scores(scores)
        weakest = min(avg, key=avg.get) if avg else "relevance"
        if not turns:
            focus = "high-signal role-specific baseline"
        elif avg.get("technical", 100) < 60:
            focus = "technical depth and reasoning"
        elif avg.get("evidence", 100) < 60:
            focus = "resume-grounded evidence and ownership"
        elif avg.get("communication", 100) < 60:
            focus = "concise communication and structure"
        elif avg.get("relevance", 100) < 60:
            focus = "directly answering the question"
        else:
            focus = "progressively harder follow-up"
        return {
            "mode": mode,
            "duration": duration,
            "focus": focus,
            "weakest_dimension": weakest,
            "turns_completed": len(turns),
            "categories": categories or ["Technical & Role-Specific 💻"],
            "remaining_minutes": remaining_minutes,
            "target_questions": target_questions,
        }


class InterviewerAgent:
    def __init__(self, gateway: GroqGateway):
        self.gateway = gateway

    def ask(self, evidence: dict, research: dict | None, plan: dict, target_role: str, industry: str, mode: str, company: str = "") -> str:
        system = (
            "You are a realistic human interviewer. Ask exactly ONE concise question. "
            "Ground it in the target role, JD requirements and candidate evidence. "
            "Never state an unsupported candidate fact. Do not ask for a resume summary. "
            "Prefer practical questions with clear evaluation signals."
        )
        user = f"""
Target role: {target_role}
Industry: {industry}
Mode: {mode}
Company: {company or "Not specified"}
Allowed categories: {safe_clamp(json.dumps(plan.get("categories", [])), 1800)}
Strategy focus: {plan['focus']}
Remaining time: {plan.get("remaining_minutes", "unknown")} minutes
Target question count: {plan.get("target_questions", "adaptive")}
Candidate evidence: {safe_clamp(json.dumps(evidence.get('candidate_facts', [])), 4500)}
JD requirements: {safe_clamp(json.dumps(evidence.get('jd_requirements', [])), 3500)}
External research (not candidate evidence): {safe_clamp(json.dumps(research or {}), 1800)}
Choose the most useful category from the allowed categories and ask one realistic interview question only. Return only the question text.
"""
        return self.gateway.chat_text(system, user, max_tokens=180)

    # Backward-compatible app-facing name used by the Streamlit UI.
    def ask_question(self, evidence: dict, research: dict | None, plan: dict, target_role: str, industry: str, mode: str, company: str = "") -> str:
        return self.ask(evidence, research, plan, target_role, industry, mode, company=company)


class CoachAgent:
    def __init__(self, gateway: GroqGateway):
        self.gateway = gateway

    def evaluate(self, question: str, answer: str, evidence: dict, target_role: str, mode: str, answer_length: str) -> dict[str, Any]:
        length_map = {"Short": "60-90", "Standard": "100-150", "Detailed": "140-180"}
        system = (
            "You are a strict but constructive interview coach. Evaluate only what is supported by the answer and candidate evidence. "
            "Do not invent employers, projects, technologies, dates, metrics, titles, certifications or responsibilities. "
            "Return valid JSON with scores 0-100."
        )
        user = f"""
Role: {target_role}
Mode: {mode}
Question: {safe_clamp(question, 2500)}
Candidate answer: {safe_clamp(answer, 5000)}
Candidate evidence only: {safe_clamp(json.dumps(evidence.get('candidate_facts', [])), 5000)}
JD requirements: {safe_clamp(json.dumps(evidence.get('jd_requirements', [])), 3500)}

JSON schema:
{{
  "scores": {{"technical":0,"relevance":0,"evidence":0,"communication":0,"structure":0,"confidence":0}},
  "overall": 0,
  "strengths": [],
  "missing_points": [],
  "verification_notes": [],
  "practice_answer": "{length_map[answer_length]} words; improve structure without adding unsupported facts",
  "next_improvement": ""
}}
"""
        result = self.gateway.chat_json(system, user, max_tokens=900)
        scores = result.get("scores", {})
        for key in ["technical", "relevance", "evidence", "communication", "structure", "confidence"]:
            scores[key] = max(0, min(100, int(scores.get(key, 0))))
        result["scores"] = scores
        result["overall"] = max(0, min(100, int(result.get("overall", round(sum(scores.values()) / len(scores))))))
        return result
