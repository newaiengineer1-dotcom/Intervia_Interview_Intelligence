import base64
import json
import os
import time
from typing import Any

from groq import Groq


# ============================================================
# GROQ MODEL CONFIGURATION
# ============================================================

# Preferred order.
# The gateway will check what the current API key can actually access.
PREFERRED_CHAT_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

DEFAULT_CHAT_MODEL = "llama-3.1-8b-instant"
DEFAULT_WHISPER_MODEL = "whisper-large-v3-turbo"


# ============================================================
# GROQ GATEWAY
# ============================================================

class GroqGateway:
    """
    Central Groq gateway.

    Responsibilities:
    - Store the API key supplied by the Streamlit UI.
    - Discover models available to that API key.
    - Automatically select an accessible chat model.
    - Send chat requests.
    - Transcribe audio.
    - Optionally analyze camera images.
    """

    def __init__(self, api_key: str):
        api_key = (api_key or "").strip()

        if not api_key:
            raise ValueError("Groq API key is required.")

        self.api_key = api_key

        self.client = Groq(
            api_key=self.api_key
        )

        self.available_models = []
        self.chat_model = None

        self._discover_models()

    # --------------------------------------------------------
    # MODEL DISCOVERY
    # --------------------------------------------------------

    def _discover_models(self):
        """
        Ask Groq which models are available to this API key.

        We intentionally do NOT assume that one particular model
        is accessible.
        """

        try:
            response = self.client.models.list()

            models = getattr(response, "data", []) or []

            discovered = []

            for model in models:
                model_id = getattr(model, "id", None)

                if model_id:
                    discovered.append(str(model_id))

            self.available_models = discovered

        except Exception as exc:
            # Do not expose the raw Groq exception in the dashboard.
            #
            # If model discovery itself fails, we still keep a
            # fallback model so the actual chat request can produce
            # the meaningful API response.
            self.available_models = []

        self.chat_model = self._choose_chat_model()

    # --------------------------------------------------------
    # CHOOSE MODEL
    # --------------------------------------------------------

    def _choose_chat_model(self):
        """
        Select the first preferred model that appears in Groq's
        model list.

        If discovery failed, use the configured environment model
        or a safe default.
        """

        configured_model = (
            os.getenv("GROQ_LLM_MODEL")
            or os.getenv("GROQ_MODEL")
            or ""
        ).strip()

        # First priority:
        # explicitly configured model, but only if discovered.
        if configured_model:
            if not self.available_models:
                return configured_model

            if configured_model in self.available_models:
                return configured_model

        # Second priority:
        # preferred models.
        if self.available_models:

            for model in PREFERRED_CHAT_MODELS:
                if model in self.available_models:
                    return model

            # Last discovered model that isn't an obvious
            # transcription/guard model.
            excluded_words = [
                "whisper",
                "guard",
                "safeguard",
                "tts",
                "speech",
                "embed",
            ]

            for model in self.available_models:
                lower = model.lower()

                if not any(
                    word in lower
                    for word in excluded_words
                ):
                    return model

        # Final fallback.
        return configured_model or DEFAULT_CHAT_MODEL

    # --------------------------------------------------------
    # PUBLIC MODEL INFO
    # --------------------------------------------------------

    def get_model(self):
        return self.chat_model

    def get_available_models(self):
        return list(self.available_models)

    # --------------------------------------------------------
    # CHAT
    # --------------------------------------------------------

    def chat(
        self,
        messages,
        model=None,
        temperature=0.2,
        max_tokens=1200,
    ):
        """
        Send a chat completion through the automatically selected
        Groq model.
        """

        selected_model = (
            model
            or self.chat_model
            or DEFAULT_CHAT_MODEL
        )

        # Remove unsupported/empty messages.
        clean_messages = []

        for message in messages:
            if not isinstance(message, dict):
                continue

            role = message.get("role")
            content = message.get("content")

            if role not in {
                "system",
                "user",
                "assistant",
            }:
                continue

            if content is None:
                continue

            clean_messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        if not clean_messages:
            raise ValueError(
                "No valid messages were supplied to Groq."
            )

        # Retry only temporary failures.
        last_error = None

        for attempt in range(3):

            try:
                response = self.client.chat.completions.create(
                    model=selected_model,
                    messages=clean_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                return response

            except Exception as exc:
                last_error = exc

                error_text = str(exc).lower()

                # Don't repeatedly retry authentication/
                # permission errors.
                if (
                    "403" in error_text
                    or "401" in error_text
                    or "permission" in error_text
                    or "unauthorized" in error_text
                    or "access denied" in error_text
                ):
                    raise

                # Retry rate-limit and temporary server errors.
                retryable = (
                    "429" in error_text
                    or "rate limit" in error_text
                    or "timeout" in error_text
                    or "500" in error_text
                    or "502" in error_text
                    or "503" in error_text
                    or "504" in error_text
                )

                if not retryable:
                    raise

                if attempt < 2:
                    time.sleep(2 ** attempt)

        raise last_error

    # --------------------------------------------------------
    # CHAT TEXT HELPER
    # --------------------------------------------------------

    def generate(
        self,
        messages,
        temperature=0.2,
        max_tokens=1200,
    ):

        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content.strip()

    # --------------------------------------------------------
    # AUDIO TRANSCRIPTION
    # --------------------------------------------------------

    def transcribe(
        self,
        audio_bytes,
        filename="answer.wav",
        model=None,
    ):

        selected_model = (
            model
            or os.getenv(
                "GROQ_WHISPER_MODEL",
                DEFAULT_WHISPER_MODEL,
            )
        )

        audio_file = (
            filename,
            audio_bytes,
        )

        result = self.client.audio.transcriptions.create(
            file=audio_file,
            model=selected_model,
        )

        text = getattr(result, "text", "")

        return (text or "").strip()

    # --------------------------------------------------------
    # CAMERA ANALYSIS
    # --------------------------------------------------------

    def analyze_camera(
        self,
        image_bytes,
        mime_type="image/jpeg",
    ):
        """
        Optional image analysis.

        If the automatically selected model does not support
        image input, return a safe unavailable response instead
        of crashing the interview.
        """

        if not image_bytes:
            return {
                "available": False,
                "message": "No camera image supplied.",
            }

        try:
            encoded = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            data_url = (
                f"data:{mime_type};base64,{encoded}"
            )

            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Review only observable presentation "
                                    "cues such as camera framing, lighting, "
                                    "and whether the face is visibly centered. "
                                    "Do not infer emotions, personality, "
                                    "health, identity, or psychological state."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url
                                },
                            },
                        ],
                    }
                ],
                temperature=0,
                max_tokens=300,
            )

            text = (
                response.choices[0]
                .message
                .content
                .strip()
            )

            return {
                "available": True,
                "feedback": text,
            }

        except Exception:
            return {
                "available": False,
                "message": (
                    "Camera analysis is unavailable "
                    "for the currently selected Groq model."
                ),
            }


# ============================================================
# EVIDENCE AGENT
# ============================================================

class EvidenceAgent:

    def __init__(self, gateway=None):
        self.gateway = gateway

    def build(
        self,
        resume_text,
        jd_text,
        target_role,
    ):

        resume_text = (resume_text or "").strip()
        jd_text = (jd_text or "").strip()

        if not resume_text and not jd_text:
            return {
                "candidate_facts": [],
                "jd_requirements": [],
                "matches": [],
                "gaps": [],
            }

        # Use Groq when a gateway is available.
        if self.gateway:

            prompt = f"""
Create an evidence-grounded interview evidence pack.

Target role:
{target_role}

Candidate resume:
{resume_text[:12000]}

Job description:
{jd_text[:12000]}

Return ONLY valid JSON:

{{
  "candidate_facts": [],
  "jd_requirements": [],
  "matches": [],
  "gaps": []
}}

Rules:
- Never invent candidate experience.
- Never claim a skill exists unless supported by the resume.
- Clearly separate unknown information.
- Keep each item concise.
"""

            result = self.gateway.generate(
                [
                    {
                        "role": "system",
                        "content": (
                            "You create factual evidence packs "
                            "for interview preparation."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0,
                max_tokens=1800,
            )

            try:
                data = json.loads(result)

                return {
                    "candidate_facts": data.get(
                        "candidate_facts",
                        [],
                    ),
                    "jd_requirements": data.get(
                        "jd_requirements",
                        [],
                    ),
                    "matches": data.get(
                        "matches",
                        [],
                    ),
                    "gaps": data.get(
                        "gaps",
                        [],
                    ),
                }

            except Exception:
                pass

        # Safe fallback if JSON generation fails.
        return {
            "candidate_facts": [
                line.strip()
                for line in resume_text.splitlines()
                if line.strip()
            ][:20],
            "jd_requirements": [
                line.strip()
                for line in jd_text.splitlines()
                if line.strip()
            ][:20],
            "matches": [],
            "gaps": [],
        }


# ============================================================
# RESEARCH AGENT
# ============================================================

class ResearchAgent:

    def __init__(self, gateway):
        self.gateway = gateway

    def run(
        self,
        target_role,
        industry,
        jd_text,
        company="",
        company_track="",
    ):

        prompt = f"""
Prepare concise interview research.

Target role:
{target_role}

Industry:
{industry}

Company:
{company or "Not specified"}

Company research track:
{company_track or "Not specified"}

Job description:
{jd_text[:8000]}

Provide:
1. Important role themes
2. Likely interview focus areas
3. Relevant industry topics
4. Company-specific considerations if known
5. Questions the candidate should prepare for

Do not invent company facts.
Clearly identify uncertain information.
"""

        return self.gateway.generate(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a career and interview "
                        "research assistant."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=1200,
        )


# ============================================================
# STRATEGY AGENT
# ============================================================

class StrategyAgent:

    def plan(
        self,
        turns,
        mode,
        duration_label,
        evidence,
        categories=None,
        remaining_minutes=None,
        target_questions=None,
    ):

        categories = categories or []

        completed = len(turns)

        recent_categories = [
            t.get("category", "")
            for t in turns[-5:]
        ]

        return {
            "mode": mode,
            "duration": duration_label,
            "categories": categories,
            "completed_questions": completed,
            "recent_categories": recent_categories,
            "remaining_minutes": remaining_minutes,
            "target_questions": target_questions,
            "next_priority": (
                categories[
                    completed % len(categories)
                ]
                if categories
                else "General"
            ),
            "evidence_available": bool(evidence),
        }


# ============================================================
# INTERVIEWER AGENT
# ============================================================

class InterviewerAgent:

    def __init__(self, gateway):
        self.gateway = gateway

    def ask_question(
        self,
        evidence,
        research,
        plan,
        target_role,
        industry,
        mode,
        company="",
    ):

        evidence = evidence or {}
        research = research or {}

        candidate_facts = evidence.get(
            "candidate_facts",
            [],
        )

        jd_requirements = evidence.get(
            "jd_requirements",
            [],
        )

        matches = evidence.get(
            "matches",
            [],
        )

        gaps = evidence.get(
            "gaps",
            [],
        )

        previous_questions = plan.get(
            "recent_categories",
            [],
        )

        category = plan.get(
            "next_priority",
            "General",
        )

        prompt = f"""
You are an adaptive AI interviewer.

Target role:
{target_role}

Interview mode:
{mode}

Company:
{company or "Not specified"}

Next category:
{category}

Candidate evidence:
{json.dumps(candidate_facts[:15], ensure_ascii=False)}

Job requirements:
{json.dumps(jd_requirements[:15], ensure_ascii=False)}

Matched evidence:
{json.dumps(matches[:10], ensure_ascii=False)}

Known gaps:
{json.dumps(gaps[:10], ensure_ascii=False)}

Recent categories:
{json.dumps(previous_questions, ensure_ascii=False)}

Research:
{str(research)[:5000]}

Create ONE realistic interview question.

Rules:
- Do not invent candidate experience.
- Do not ask multiple questions.
- Keep it practical.
- Ground the question in the selected category.
- Avoid repeating recent question themes.
- Return JSON only.

Format:

{{
  "category": "{category}",
  "question": "..."
}}
"""

        result = self.gateway.generate(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a professional adaptive "
                        "interviewer."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.4,
            max_tokens=500,
        )

        try:
            data = json.loads(result)

            question = str(
                data.get("question", "")
            ).strip()

            selected_category = str(
                data.get("category", category)
            ).strip()

            if question:
                return {
                    "category": selected_category,
                    "question": question,
                }

        except Exception:
            pass

        # Fallback question.
        return {
            "category": category,
            "question": (
                f"Tell me about a specific example "
                f"that demonstrates your experience "
                f"with {category}."
            ),
        }


# ============================================================
# COACH AGENT
# ============================================================

class CoachAgent:

    def __init__(self, gateway):
        self.gateway = gateway

    def evaluate(
        self,
        question,
        answer,
        evidence,
        target_role,
        mode,
        answer_length="Standard",
    ):

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

Evidence:
{json.dumps(evidence or {}, ensure_ascii=False)[:9000]}

Return ONLY JSON:

{{
  "scores": {{
    "technical": 0,
    "relevance": 0,
    "evidence": 0,
    "communication": 0,
    "structure": 0,
    "confidence": 0
  }},
  "overall": 0,
  "strengths": [],
  "missing_points": [],
  "verification_notes": [],
  "practice_answer": "",
  "next_improvement": ""
}}

Scoring:
0-10 for each dimension.

Important:
- Do not invent facts about the candidate.
- Distinguish unsupported claims from verified evidence.
- Give practical interview coaching.
- The practice answer must remain consistent with the available evidence.
"""

        result = self.gateway.generate(
            [
                {
                    "role": "system",
                    "content": (
                        "You are an evidence-grounded "
                        "interview performance coach."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=1800,
        )

        try:
            data = json.loads(result)

            scores = data.get(
                "scores",
                {},
            )

            return {
                "scores": {
                    "technical": scores.get(
                        "technical",
                        0,
                    ),
                    "relevance": scores.get(
                        "relevance",
                        0,
                    ),
                    "evidence": scores.get(
                        "evidence",
                        0,
                    ),
                    "communication": scores.get(
                        "communication",
                        0,
                    ),
                    "structure": scores.get(
                        "structure",
                        0,
                    ),
                    "confidence": scores.get(
                        "confidence",
                        0,
                    ),
                },
                "overall": data.get(
                    "overall",
                    0,
                ),
                "strengths": data.get(
                    "strengths",
                    [],
                ),
                "missing_points": data.get(
                    "missing_points",
                    [],
                ),
                "verification_notes": data.get(
                    "verification_notes",
                    [],
                ),
                "practice_answer": data.get(
                    "practice_answer",
                    "",
                ),
                "next_improvement": data.get(
                    "next_improvement",
                    "",
                ),
            }

        except Exception:
            return {
                "scores": {
                    "technical": 0,
                    "relevance": 0,
                    "evidence": 0,
                    "communication": 0,
                    "structure": 0,
                    "confidence": 0,
                },
                "overall": 0,
                "strengths": [],
                "missing_points": [
                    "The AI evaluation could not be parsed."
                ],
                "verification_notes": [],
                "practice_answer": "",
                "next_improvement": (
                    "Please try the answer again."
                ),
            }
