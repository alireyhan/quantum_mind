import re
import time
import logging
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

class TranslationService:
    @staticmethod
    def translate_script(script: str, target_lang: str) -> str:
        """
        Translates a hypnotherapy script to the target language line by line
        using deep-translator (Google Translator API).
        Preserves [pause: Ns] markers exactly as they are.
        """
        if target_lang.lower() == 'en' or not target_lang:
            return script
            
        logger.info('Translating script to %s...', target_lang)
        try:
            translator = GoogleTranslator(source='auto', target=target_lang)
        except Exception as e:
            logger.error("Failed to initialize GoogleTranslator: %s", e)
            return script
        
        # Split by pause markers to keep them completely intact
        pause_pattern = r'(\[pause(?::\s*\d+s)?\])'
        parts = re.split(pause_pattern, script, flags=re.IGNORECASE)
        
        translated_parts = []
        for part in parts:
            if not part:
                continue
                
            if re.match(r'^\[pause(?::\s*\d+s)?\]$', part, flags=re.IGNORECASE):
                # Keep pause marker exactly as is
                translated_parts.append(part)
            elif part.strip():
                # Translate text line by line to avoid large payload failures
                lines = part.split('\n')
                translated_lines = []
                for i, line in enumerate(lines):
                    if line.strip():
                        try:
                            translated_text = translator.translate(line)
                            translated_lines.append(translated_text)
                            # Optional sleep to avoid rate limiting
                            time.sleep(0.1)
                        except Exception as e:
                            logger.error('Translation error on line %d: %s', i, e)
                            translated_lines.append(line)  # Fallback to original
                    else:
                        translated_lines.append('')
                
                translated_parts.append('\n'.join(translated_lines))
            else:
                # Just whitespace/newlines
                translated_parts.append(part)
                
        logger.info('Script translation complete.')
        return ''.join(translated_parts)
