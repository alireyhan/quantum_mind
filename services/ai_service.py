import logging
import httpx
from django.conf import settings
from typing import Dict, Any

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Wraps the OpenAI API to generate hypnotherapy scripts
    and perform problem category diagnosis from intake data.
    """

    MODEL = 'gpt-4o'
    BASE_URL = 'https://api.openai.com/v1/chat/completions'

    # ── Token budget: ~900 tokens/minute of audio at average speech rate ──
    # This accounts for both spoken words AND the [pause: Ns] markers embedded in the script.
    # 10 min  → ~9,000 tokens   (+ system overhead ~2,000) → 11,000
    # 25 min  → ~22,500 tokens  → 24,000
    # 30 min  → ~27,000 tokens  → 29,000
    # gpt-4o supports up to 16,384 output tokens; gpt-4o-2024-11-20 and later support up to 16,384.
    # We cap at 16,000 to stay within the model's hard output limit.
    TOKENS_PER_MINUTE = 900
    TOKEN_OVERHEAD = 2000     # prompt echoing + formatting overhead
    MAX_OUTPUT_CAP = 16000    # hard cap for gpt-4o output tokens
    DEFAULT_MAX_TOKENS = 11000

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    @classmethod
    def tokens_for_duration(cls, session_duration_minutes: int) -> int:
        """Calculate the required max_tokens for a given session duration."""
        needed = int(session_duration_minutes * cls.TOKENS_PER_MINUTE) + cls.TOKEN_OVERHEAD
        return min(needed, cls.MAX_OUTPUT_CAP)

    @classmethod
    def needs_multi_pass(cls, session_duration_minutes: int) -> bool:
        """Return True if the session is too long to generate in a single API call."""
        return int(session_duration_minutes * cls.TOKENS_PER_MINUTE) + cls.TOKEN_OVERHEAD > cls.MAX_OUTPUT_CAP

    async def generate_script(self, prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
        """
        Send the filled prompt to OpenAI and return the generated script text.
        Uses async httpx for non-blocking I/O inside Celery tasks (via asyncio.run).
        """
        payload = {
            'model': self.MODEL,
            'max_tokens': max_tokens,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt,
                }
            ],
            'temperature': 0.7,
        }

        logger.info('Sending prompt to OpenAI (%d chars)', len(prompt))

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(self.BASE_URL, json=payload, headers=self._headers)
            response.raise_for_status()
            data = response.json()

        finish_reason = data['choices'][0].get('finish_reason', 'unknown')
        script = data['choices'][0]['message']['content']
        logger.info(
            'OpenAI returned script (%d chars, finish_reason=%s)',
            len(script), finish_reason,
        )
        return script

    async def generate_script_multipass(self, prompt: str, session_duration_minutes: int) -> str:
        """
        For sessions longer than ~15 minutes, a single gpt-4o call is capped at
        16,384 output tokens (~15 min of audio). This method issues two sequential
        API calls — each capped at MAX_OUTPUT_CAP — and concatenates the results.

        Pass 1: Generate the script through Phase 6 (core change work).
        Pass 2: Continue from the exact cutoff point to complete Phases 7–11.
        """
        pass_1_tokens = self.MAX_OUTPUT_CAP

        # ── Pass 1 ────────────────────────────────────────────────────────
        continuation_instruction = (
            "\n\n[SYSTEM NOTE: You are writing a long hypnotherapy script. "
            "Generate the first half of this script, covering the Induction, Deepening, "
            "Resource Activation, Nested Loop Metaphors, and Core Change Work phases. "
            "Write as much rich, detailed content as possible. "
            "Stop mid-sentence if you reach the token limit — the script will be continued in the next pass.]"
        )
        prompt_pass_1 = prompt + continuation_instruction

        logger.info('Multi-pass generation: starting Pass 1 (%d max_tokens)...', pass_1_tokens)
        part_1 = await self.generate_script(prompt_pass_1, max_tokens=pass_1_tokens)
        logger.info('Pass 1 complete: %d chars generated.', len(part_1))

        # ── Pass 2: continue from exact cutoff ───────────────────────────
        pass_2_tokens = self.MAX_OUTPUT_CAP

        continuation_prompt = (
            f"{prompt}\n\n"
            f"[SYSTEM NOTE: This is a CONTINUATION of a hypnotherapy script that was started "
            f"below. Continue seamlessly from where the script was cut off. Do NOT restart or "
            f"repeat any content from Pass 1. Pick up mid-sentence if necessary and complete "
            f"all remaining phases through to the Gentle Emergence and final goodbye. "
            f"Remaining phases to complete: Identity Installation, Behavioural Rehearsal, "
            f"Future Pacing, Integration, and Gentle Emergence.]\n\n"
            f"--- SCRIPT SO FAR (continue from the end of this) ---\n"
            f"{part_1}\n"
            f"--- END OF SCRIPT SO FAR — CONTINUE FROM HERE ---"
        )

        logger.info('Multi-pass generation: starting Pass 2 (%d max_tokens)...', pass_2_tokens)
        part_2 = await self.generate_script(continuation_prompt, max_tokens=pass_2_tokens)
        logger.info('Pass 2 complete: %d chars generated.', len(part_2))

        full_script = part_1.rstrip() + '\n\n' + part_2.lstrip()
        logger.info(
            'Multi-pass script assembled: %d total chars (%d + %d)',
            len(full_script), len(part_1), len(part_2),
        )
        return full_script

    def diagnose_problem_category(self, intake_data: Dict[str, Any]) -> str:
        """
        Keyword-scoring heuristic to auto-detect the primary problem category
        from the user's intake text. Result is injected into the prompt as
        {{problemCategory}} and stored on IntakeResponse.problem_category.
        """
        issue = (intake_data.get('main_issue') or '').lower()
        triggers_list = intake_data.get('triggers') or []
        triggers = ' '.join(triggers_list if isinstance(triggers_list, list) else []).lower()
        symptoms_list = intake_data.get('symptoms') or []
        symptoms = ' '.join(symptoms_list if isinstance(symptoms_list, list) else []).lower()
        text = f'{issue} {triggers} {symptoms}'

        category_keywords: Dict[str, list] = {
            'sleep':        ['sleep', 'insomnia', 'tired', 'rest', 'night', 'wake', 'fatigue'],
            'anxiety':      ['anxiety', 'panic', 'worry', 'fear', 'nervous', 'stress', 'overwhelm'],
            'depression':   ['depression', 'sad', 'hopeless', 'empty', 'numb', 'low mood', 'worthless'],
            'trauma':       ['trauma', 'ptsd', 'flashback', 'abuse', 'accident', 'nightmare', 'trigger'],
            'addiction':    ['addict', 'smoke', 'drink', 'alcohol', 'craving', 'habit', 'substance'],
            'performance':  ['performance', 'procrastination', 'focus', 'motivation', 'productivity', 'block'],
            'relationship': ['relationship', 'partner', 'social', 'lonely', 'connection', 'breakup'],
            'self_esteem':  ['confidence', 'worthless', 'shame', 'guilt', 'self-worth', 'inadequate'],
            'grief':        ['grief', 'loss', 'death', 'mourning', 'bereave', 'missing'],
            'anger':        ['anger', 'rage', 'frustration', 'irritable', 'temper', 'explosive'],
        }

        scores: Dict[str, int] = {cat: 0 for cat in category_keywords}
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                scores[category] += text.count(keyword)

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return 'general'
        logger.debug('Problem category diagnosed: %s (score=%d)', best, scores[best])
        return best
