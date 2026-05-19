import logging
import httpx
from django.conf import settings
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ClaudeService:
    """
    Wraps the Anthropic Claude API to generate hypnotherapy scripts
    and perform problem category diagnosis from intake data.
    """

    MODEL = 'claude-3-5-sonnet-20241022'
    BASE_URL = 'https://api.anthropic.com/v1/messages'

    # ── Token budget: ~750 tokens/minute of audio at average speech rate ──
    # 10 min  → ~7,500 tokens   (+ system overhead ~2,000) → 10,000
    # 30 min  → ~22,500 tokens  → 25,000
    # 45 min  → ~33,750 tokens  → 36,000
    DEFAULT_MAX_TOKENS = 36_000

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        }

    async def generate_script(self, prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
        """
        Send the filled prompt to Claude and return the generated script text.
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

        logger.info('Sending prompt to Claude (%d chars)', len(prompt))

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(self.BASE_URL, json=payload, headers=self._headers)
            response.raise_for_status()
            data = response.json()

        script = data['content'][0]['text']
        logger.info('Claude returned script (%d chars)', len(script))
        return script

    def diagnose_problem_category(self, intake_data: Dict[str, Any]) -> str:
        """
        Keyword-scoring heuristic to auto-detect the primary problem category
        from the user's intake text. Result is injected into the prompt as
        {{problemCategory}} and stored on IntakeResponse.problem_category.
        """
        issue = intake_data.get('main_issue', '').lower()
        triggers = ' '.join(intake_data.get('triggers', [])).lower()
        symptoms = ' '.join(intake_data.get('symptoms', [])).lower()
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
