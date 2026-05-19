import re
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class PromptTemplateEngine:
    """
    Loads the hypnotherapy prompt template and fills all {{variables}},
    processes {{#if variable}}...{{/if}} conditional blocks,
    and injects adaptive profile + program context sections.
    """

    def __init__(self):
        self.template_path = getattr(
            settings, 'PROMPT_TEMPLATE_PATH',
            settings.BASE_DIR / 'templates' / 'hypnotherapy_prompt.txt'
        )

    def load_template(self) -> str:
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def fill_template(
        self,
        variables: Dict[str, Any],
        profile_context: Optional[Dict] = None,
        program_context: Optional[Dict] = None,
    ) -> str:
        template = self.load_template()

        # 1. Process conditionals first (they may contain variables inside)
        template = self._process_conditionals(template, variables)

        # 2. Fill simple {{variable}} placeholders
        for key, value in variables.items():
            placeholder = f'{{{{{key}}}}}'
            if value is None:
                value = ''
            elif isinstance(value, bool):
                value = 'yes' if value else 'no'
            elif isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            template = template.replace(placeholder, str(value))

        # 3. Inject adaptive profile block
        if profile_context:
            profile_block = self._build_profile_block(profile_context)
        else:
            profile_block = ''
        template = template.replace('{{ADAPTIVE_PROFILE}}', profile_block)

        # 4. Inject program context block
        if program_context:
            prog_block = self._build_program_block(program_context)
        else:
            prog_block = ''
        template = template.replace('{{PROGRAM_CONTEXT}}', prog_block)

        # 5. Clean up any remaining unfilled placeholders
        template = re.sub(r'\{\{[^}]+\}\}', '', template)

        return template.strip()

    def _process_conditionals(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace {{#if variable}}...{{/if}} blocks conditionally."""
        pattern = r'\{\{#if (\w+)\}\}(.*?)\{\{/if\}\}'

        def replace_conditional(match):
            var_name = match.group(1)
            content = match.group(2)
            value = variables.get(var_name)

            if value is None or value == '' or value is False:
                return ''
            if isinstance(value, list) and len(value) == 0:
                return ''
            # Truthy: include block
            return content

        return re.sub(pattern, replace_conditional, template, flags=re.DOTALL)

    def _build_profile_block(self, profile: Dict) -> str:
        lines = [
            '## Returning User Adaptive Context',
            '',
            'This user has completed previous sessions. Personalise this session accordingly.',
        ]
        if profile.get('most_effective_techniques'):
            techs = ', '.join(profile['most_effective_techniques'])
            lines.append(f'- Most effective techniques for this user: **{techs}**. Prioritise these.')
        if profile.get('least_effective_techniques'):
            techs = ', '.join(profile['least_effective_techniques'])
            lines.append(f'- De-emphasise or omit: {techs}.')
        if profile.get('key_themes'):
            themes = ', '.join(profile['key_themes'])
            lines.append(f'- Key recurring themes in their journey: {themes}.')
        if profile.get('session_count'):
            lines.append(
                f'- They have completed {profile["session_count"]} sessions. '
                'Reference their progress. Acknowledge how far they have come.'
            )
        lines.append('- Build on what has already worked. Avoid repetition of previous sessions.')
        return '\n'.join(lines)

    def _build_program_block(self, context: Dict) -> str:
        day = context.get('day', 1)
        total = context.get('total_days', 1)
        name = context.get('program_name', 'the program')
        focus = context.get('focus_technique', '')

        lines = [
            f'## Program Context: {name}',
            '',
            f'This is Day {day} of {total} in the **{name}** program.',
            f'Acknowledge which day they are on and celebrate how far they have come.',
            'Create a sense of progressive deepening — each session builds on the last.',
            'Reference the cumulative transformation occurring beneath the surface.',
        ]
        if focus:
            lines.append(f'Today\'s primary therapeutic focus: **{focus}**.')
        return '\n'.join(lines)

    # ── Convenience passthrough (used by tasks.py) ─────────────────────────
    def strip_non_spoken_text(self, script: str) -> str:
        """Delegate to AudioService-compatible stripping (imported lazily to avoid circular)."""
        from services.audio_service import AudioService
        return AudioService().strip_non_spoken_text(script)

    def split_text_into_chunks(self, text: str):
        """Delegate to AudioService-compatible chunking."""
        from services.audio_service import AudioService
        return AudioService().split_text_into_chunks(text)
