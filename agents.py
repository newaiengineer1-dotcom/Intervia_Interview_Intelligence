import base64
import json
import os
import time
from typing import Any, Dict, List, Optional

from groq import Groq


DEFAULT_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)


def _text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def _json_object(value: str) -> Dict[str, Any]:
    text = _text(value)

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        try:
            return json.loads(
                text[start : end + 1]
            )
        except Exception:
            pass

    return {}


class GroqGateway:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
    ):
        if not api_key:
            raise ValueError(
                "Groq API key is required."
            )

        self.api_key = api_key
        self.model = model

        self.client = Groq(
            api_key=api_key
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 3000,
    ) -> str:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return _text(
            response.choices[0]
            .message
            .content
        )

    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "answer.wav",
    ) -> str:

        response = self.client.audio.transcriptions.create(
            file=(
                filename,
                audio_bytes,
            ),
            model="whisper-large-v3",
        )

        return _text(
            getattr(
                response,
                "text",
                "",
            )
        )

    def analyze_camera(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ) -> Dict[str, Any]:

        encoded = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this interview "
                                "presentation snapshot. "
                                "Only comment on visible, "
                                "observable presentation cues "
                                "such as posture, framing, "
                                "lighting, and apparent "
                                "engagement. Do not infer "
                                "protected or sensitive "
                                "personal characteristics. "
                                "Return concise JSON with "
                                "keys: available, strengths, "
                                "improvements."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:{mime_type};"
                                    f"base64,{encoded}"
                                )
                            },
                        },
                    ],
                }
            ],
            temperature=0.1,
            max_tokens=800,
        )

        result = _json_object(
            response.choices[0]
            .message
            .content
        )

        if not result:
            return {
                "available": True,
                "feedback": _text(
                    response.choices[0]
                    .message
                    .content
                ),
            }

        result["available"] = True

        return result


class EvidenceAgent:

    def build(
        self,
        cv_text: str,
        jd_text: str,
        target_role: str,
        industry: str = "",
    ) -> Dict[str, Any]:

        cv_text = _text(cv_text)
        jd_text = _text(jd_text)

        client = Groq(
            api_key=os.getenv(
                "GROQ_API_KEY",
                "",
            )
        )

        # This agent is normally called from the app
        # with the user's API key. If an environment key
        # is unavailable, create a lightweight grounded
        # evidence structure without making an API call.

        if not os.getenv("GROQ_API_KEY"):
            return self._fallback(
                cv_text,
                jd_text,
                target_role,
            )

        prompt = f"""
You are an evidence extraction assistant.

Target role:
{target_role}

CV:
{cv_text}

Job description:
{jd_text}

Return ONLY valid JSON with these keys:

candidate_facts
jd_requirements
matches
gaps

Each value must be a list of concise factual statements.

Do not invent information.
If something is unknown, put it in gaps.
"""

        try:

            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.1,
                max_tokens=2500,
            )

            result = _json_object(
                response.choices[0]
                .message
                .content
            )

            if result:
                return result

        except Exception:
            pass

        return self._fallback(
            cv_text,
            jd_text,
            target_role,
        )

    @staticmethod
    def _fallback(
        cv_text: str,
        jd_text: str,
        target_role: str,
    ) -> Dict[str, Any]:

        return {
            "candidate_facts": [
                f"Target role: {target_role}"
            ],
            "jd_requirements": [
                "Job description provided by candidate."
            ],
            "matches": [],
            "gaps": [
                "Automated evidence comparison "
                "was not available."
            ],
        }


class ResearchAgent:

    def __init__(
        self,
        gateway: GroqGateway,
    ):
        self.gateway = gateway

    def run(
        self,
        target_role: str,
        industry: str,
        jd_text: str,
        company: str = "",
        company_track: str = "",
    ) -> Dict[str, Any]:

        prompt = f"""
Create a concise interview research brief.

Target role:
{target_role}

Company:
{company or "Not specified"}

Industry:
{industry}

Job description:
{jd_text}

Additional company context:
{company_track or "None"}

Return JSON with:
company_context
role_context
likely_topics
questions_to_prepare
unknowns

Do not invent company facts.
Use "unknown" where information is unavailable.
"""

        result = _json_object(
            self.gateway.chat(
                [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.1,
                max_tokens=1800,
            )
        )

        return result or {
            "company_context": "unknown",
            "role_context": target_role,
            "likely_topics": [],
            "questions_to_prepare": [],
            "unknowns": [
                "Research response could not be parsed."
            ],
        }


class StrategyAgent:

    def plan(
        self,
        turns: List[Dict[str, Any]],
        mode: str,
        duration_label: str,
        evidence: Dict[str, Any],
        categories: Optional[List[str]] = None,
        remaining_minutes: float = 30,
        target_questions: int = 8,
    ) -> Dict[str, Any]:

        categories = categories or []

        completed = len(turns)

        used_categories = [
            _text(
                item.get(
                    "category",
                    "",
                )
            )
            for item in turns
        ]

        return {
            "mode": mode,
            "duration": duration_label,
            "categories": categories,
            "completed_questions": completed,
            "remaining_minutes": remaining_minutes,
            "target_questions": target_questions,
            "used_categories": used_categories,
            "next_focus": (
                categories[
                    completed % len(categories)
                ]
                if categories
                else "General"
            ),
        }


class InterviewerAgent:

    def __init__(
        self,
        gateway: GroqGateway,
    ):
        self.gateway = gateway

    def ask_question(
        self,
        evidence: Dict[str, Any],
        research: Optional[Dict[str, Any]],
        plan: Dict[str, Any],
        target_role: str,
        industry: str,
        mode: str,
        company: str = "",
    ) -> Dict[str, str]:

        category = plan.get(
            "next_focus",
            "General",
        )

        prompt = f"""
You are an adaptive professional interviewer.

Target role:
{target_role}

Interview mode:
{mode}

Category:
{category}

Company:
{company or "Not specified"}

Evidence:
{json.dumps(evidence, ensure_ascii=False)}

Previous research:
{json.dumps(research or {}, ensure_ascii=False)}

Previous questions:
{json.dumps(plan, ensure_ascii=False)}

Generate ONE practical interview question.

The question must be grounded in the supplied evidence.
Do not invent candidate experience.
Return ONLY JSON:

{{
  "category": "...",
  "question": "..."
}}
"""

        result = _json_object(
            self.gateway.chat(
                [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.4,
                max_tokens=700,
            )
        )

        question = _text(
            result.get(
                "question",
                "",
            )
        )

        if not question:

            question = (
                f"Tell me about your experience "
                f"relevant to {target_role}."
            )

        return {
            "category": _text(
                result.get(
                    "category",
                    category,
                )
            ),
            "question": question,
        }


class CoachAgent:

    def __init__(
        self,
        gateway: GroqGateway,
    ):
        self.gateway = gateway

    def evaluate(
        self,
        question: str,
        answer: str,
        evidence: Dict[str, Any],
        target_role: str,
        mode: str,
        answer_length: str = "Standard",
    ) -> Dict[str, Any]:

        prompt = f"""
Evaluate this interview answer.

Target role:
{target_role}

Interview mode:
{mode}

Question:
{question}

Candidate answer:
{answer}

Grounding evidence:
{json.dumps(evidence, ensure_ascii=False)}

Return ONLY valid JSON with:

overall
technical
communication
strengths
improvements
model_answer
feedback

Scores should be integers from 0 to 100.

Do not invent candidate facts.
The model_answer should be an example of how the
candidate could structure a stronger answer.
"""

        result = _json_object(
            self.gateway.chat(
                [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.2,
                max_tokens=1800,
            )
        )

        if not result:

            return {
                "overall": 0,
                "technical": 0,
                "communication": 0,
                "strengths": [],
                "improvements": [
                    "Unable to parse coaching response."
                ],
                "model_answer": "",
                "feedback": (
                    "The coaching response could not "
                    "be parsed."
                ),
            }

        return result
