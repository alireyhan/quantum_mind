import re
import logging
from typing import List
from django.conf import settings
import httpx
import io
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class AudioService:
    """
    Handles ElevenLabs TTS generation, text pre-processing,
    chunk splitting, and MP3 concatenation.
    """

    MAX_CHUNK_CHARS = 4_500   # ElevenLabs character limit per request
    MODEL_ID = 'eleven_flash_v2_5'

    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.base_url = 'https://api.elevenlabs.io/v1'

    # ── Text Pre-processing ───────────────────────────────────────────────

    def strip_non_spoken_text(self, script: str) -> str:
        """
        Remove markdown headers, stage directions, parentheticals, and pause markers
        so only the spoken words reach TTS or visual transcript.
        """
        # Remove markdown headers (# ## ###)
        script = re.sub(r'^#{1,6}\s+.*$', '', script, flags=re.MULTILINE)
        # Remove bracketed pause markers [pause: 5s] or [pause]
        script = re.sub(r'\[pause(?::\s*\d+s)?\]', '', script, flags=re.IGNORECASE)
        # Remove bracketed stage directions [pause] [deep breath] etc.
        script = re.sub(r'\[.*?\]', '', script, flags=re.DOTALL)
        # Remove parenthetical directions (pause here) (slow voice)
        script = re.sub(r'\(.*?\)', '', script, flags=re.DOTALL)
        # Remove bold/italic markdown
        script = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', script)
        # Remove horizontal rules
        script = re.sub(r'^---+$', '', script, flags=re.MULTILINE)
        # Collapse excessive blank lines
        script = re.sub(r'\n{3,}', '\n\n', script)
        return script.strip()

    def parse_script_with_pauses(self, script: str) -> List[dict]:
        """
        Parse raw script into sequential blocks of spoken text vs. programmatic silence.
        """
        # Split on [pause] or [pause: Ns] markers. Keep the capturing parentheses so the markers are in the split parts
        pause_pattern = r'(\[pause(?::\s*\d+s)?\])'
        parts = re.split(pause_pattern, script, flags=re.IGNORECASE)
        
        parsed = []
        for part in parts:
            part_str = part.strip()
            if not part_str:
                continue
                
            # Check if this part is a pause marker
            pause_match = re.match(r'^\[pause(?::\s*(\d+)s)?\]$', part_str, flags=re.IGNORECASE)
            if pause_match:
                seconds_str = pause_match.group(1)
                seconds = int(seconds_str) if seconds_str else 4  # default to 4-second pause
                parsed.append({
                    'type': 'pause',
                    'duration_ms': seconds * 1000
                })
            else:
                # It's a text block. Clean other directions first.
                cleaned = self.strip_non_spoken_text(part_str)
                if cleaned:
                    parsed.append({
                        'type': 'text',
                        'content': cleaned
                    })
        return parsed

    def split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split cleaned script at sentence boundaries so each chunk
        is within the ElevenLabs 4,500 character limit.
        """
        # Split on sentence-ending punctuation followed by whitespace
        sentences = re.split(r'(?<=[.!?…])\s+', text)
        chunks: List[str] = []
        current_parts: List[str] = []
        current_len = 0

        for sentence in sentences:
            s_len = len(sentence)

            # If a single sentence exceeds the limit, split it further at commas
            if s_len > self.MAX_CHUNK_CHARS:
                if current_parts:
                    chunks.append(' '.join(current_parts))
                    current_parts = []
                    current_len = 0
                sub_parts = re.split(r'(?<=,)\s+', sentence)
                sub_chunk: List[str] = []
                sub_len = 0
                for part in sub_parts:
                    if sub_len + len(part) > self.MAX_CHUNK_CHARS:
                        if sub_chunk:
                            chunks.append(' '.join(sub_chunk))
                        sub_chunk = [part]
                        sub_len = len(part)
                    else:
                        sub_chunk.append(part)
                        sub_len += len(part) + 1
                if sub_chunk:
                    chunks.append(' '.join(sub_chunk))
                continue

            if current_len + s_len + 1 > self.MAX_CHUNK_CHARS:
                if current_parts:
                    chunks.append(' '.join(current_parts))
                current_parts = [sentence]
                current_len = s_len
            else:
                current_parts.append(sentence)
                current_len += s_len + 1

        if current_parts:
            chunks.append(' '.join(current_parts))

        logger.info('Script split into %d chunks for TTS', len(chunks))
        return chunks

    # ── ElevenLabs API ────────────────────────────────────────────────────

    async def generate_audio_chunk(self, text: str, language: str = 'en') -> bytes:
        """Generate MP3 audio for a single text chunk via ElevenLabs."""
        url = f'{self.base_url}/text-to-speech/{self.voice_id}'

        headers = {
            'xi-api-key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'audio/mpeg',
        }

        # If language is specified and not english, use multilingual model
        model_id = self.MODEL_ID
        if language and language.lower() != 'en':
            model_id = 'eleven_multilingual_v2'

        payload = {
            'text': text,
            'model_id': model_id,
            'voice_settings': {
                'stability': 0.55,
                'similarity_boost': 0.75,
                'style': 0.10,
                'use_speaker_boost': True,
            },
            'output_format': 'mp3_44100_128',
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.content

    async def generate_full_audio(self, script: str, language: str = 'en') -> bytes:
        """
        Full pipeline:
        1. Parse script into sequential text blocks and programmatic pauses.
        2. Generate speech for text blocks via ElevenLabs.
        3. Insert precise silent AudioSegments for pauses.
        4. Concatenate all AudioSegments using pydub.
        """
        parsed_items = self.parse_script_with_pauses(script)
        combined_audio = AudioSegment.empty()
        
        for idx, item in enumerate(parsed_items, 1):
            if item['type'] == 'pause':
                duration_ms = item['duration_ms']
                logger.info('Stitching silence chunk: %d ms', duration_ms)
                silence = AudioSegment.silent(duration=duration_ms)
                combined_audio += silence
            elif item['type'] == 'text':
                text_content = item['content']
                # Split this text block into smaller chunks if it exceeds the ElevenLabs limit
                chunks = self.split_text_into_chunks(text_content)
                for chunk in chunks:
                    logger.info('Generating audio chunk (%d chars): %s...', len(chunk), chunk[:30])
                    chunk_bytes = await self.generate_audio_chunk(chunk, language=language)
                    segment = AudioSegment.from_file(io.BytesIO(chunk_bytes), format='mp3')
                    combined_audio += segment
        
        # Ensure we have at least some audio to avoid empty exports
        if len(combined_audio) == 0:
            logger.warning('Audio sequence was empty. Creating 1 second of silence.')
            combined_audio = AudioSegment.silent(duration=1000)
            
        output = io.BytesIO()
        combined_audio.export(output, format='mp3', bitrate='128k')
        logger.info('Combined audio export complete: %d bytes total', len(output.getvalue()))
        return output.getvalue()

    async def generate_background_music(self, prompt: str) -> bytes:
        """
        Generate background music/ambient sound via ElevenLabs Sound Generation API.
        We'll loop this track to fit the full session duration later.
        """
        url = f'{self.base_url}/sound-generation'
        headers = {
            'xi-api-key': self.api_key,
            'Content-Type': 'application/json',
        }
        payload = {
            'text': prompt,
            'duration_seconds': 22, # max allowed for sound-generation
            'prompt_influence': 0.3,
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.content

    def mix_audio_with_background(self, voice_bytes: bytes, music_bytes: bytes, volume_reduction: int = 15) -> bytes:
        """
        Overlays the voice track over the background music track using ffmpeg directly 
        to avoid massive RAM usage (OOM) on long 30+ min sessions.
        """
        import subprocess
        import tempfile
        import os

        vol_db = f"-{volume_reduction}dB"

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_voice, \
             tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_music, \
             tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_out:
             
            f_voice.write(voice_bytes)
            f_voice.flush()
            
            f_music.write(music_bytes)
            f_music.flush()

            cmd = [
                "ffmpeg",
                "-y",
                "-stream_loop", "-1",
                "-i", f_music.name,
                "-i", f_voice.name,
                "-filter_complex", f"[0:a]volume={vol_db}[bg];[bg][1:a]amix=inputs=2:duration=shortest[out]",
                "-map", "[out]",
                "-c:a", "libmp3lame",
                "-b:a", "128k",
                f_out.name
            ]
            
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                with open(f_out.name, "rb") as result_file:
                    return result_file.read()
            except subprocess.CalledProcessError as e:
                logger.error("FFmpeg mixing failed: %s", e.stderr.decode('utf-8', errors='ignore'))
                logger.warning("Falling back to voice-only output due to mix failure.")
                return voice_bytes
            finally:
                os.unlink(f_voice.name)
                os.unlink(f_music.name)
                os.unlink(f_out.name)
