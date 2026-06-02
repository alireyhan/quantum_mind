import logging
import asyncio
import uuid
from django.utils import timezone
from celery import shared_task
from .models import TherapySession, AudioAsset

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 60 second backoff between retries
    name='sessions.generate_session',
)
def generate_session_task(self, session_id: int):
    """
    Async-orchestrated session generation pipeline:

    1. Build the personalised prompt from the intake + adaptive profile + program context
    2. Generate the hypnotherapy script via Claude (async)
    3. Convert the script to audio via ElevenLabs TTS (async, chunked)
    4. Upload the MP3 to S3/Spaces
    5. Save all results and mark session as completed

    On failure: credits are refunded and the session is marked failed.
    """
    # ── Lazy imports to avoid circular deps ──────────────────────────────
    from services.ai_service import OpenAIService
    from services.audio_service import AudioService
    from services.storage_service import StorageService
    from services.template_service import PromptTemplateEngine
    from apps.credits.services import CreditService
    from apps.feedback.services import ProfileService

    try:
        session = TherapySession.objects.select_related(
            'user', 'intake', 'program_day__program'
        ).get(id=session_id)
    except TherapySession.DoesNotExist:
        logger.error('Session %s not found — cannot generate.', session_id)
        return

    # ── Phase 1: Build Prompt ─────────────────────────────────────────────
    try:
        session.status = TherapySession.STATUS_GENERATING_SCRIPT
        session.save(update_fields=['status'])

        intake = session.intake
        engine = PromptTemplateEngine()

        session_duration = session.duration_minutes
        target_word_count = max(1200, int(session_duration * 115))

        variables = {
            'mainIssue': intake.main_issue,
            'issueDuration': intake.issue_duration,
            'triggers': intake.triggers,
            'symptoms': intake.symptoms,
            'behaviorToChange': intake.behavior_to_change,
            'desiredEmotionalShift': intake.desired_emotional_shift,
            'successVision': intake.success_vision,
            'positiveAnchoringMemory': intake.positive_anchoring_memory,
            'interests': intake.interests,
            'workLifeEnvironment': intake.work_life_environment,
            'sessionDuration': session_duration,
            'targetWordCount': target_word_count,
            'targetWordCount_5': int(target_word_count * 0.05),
            'targetWordCount_15': int(target_word_count * 0.15),
            'targetWordCount_20': int(target_word_count * 0.20),
            'targetWordCount_35': int(target_word_count * 0.35),
            'problemCategory': intake.problem_category,
            # Advanced fields (conditional blocks)
            'repeatingThoughts': intake.repeating_thoughts,
            'negativeBeliefs': intake.negative_beliefs,
            'hasInnerConflict': intake.has_inner_conflict,
            'innerConflictDescription': intake.inner_conflict_description,
            'resistanceProtection': intake.resistance_protection,
            'bodyLocation': intake.body_location,
            'representationalSystem': intake.representational_system,
            'fearsAboutChange': intake.fears_about_change,
            'connectedToPastEvent': intake.connected_to_past_event,
            'keyAffirmations': intake.key_affirmations,
            'languageToAvoid': intake.language_to_avoid,
            'postSessionState': intake.post_session_state,
            'focusCategory': intake.focus_category,
        }

        # Adaptive profile context
        profile_service = ProfileService()
        profile_context = profile_service.build_therapeutic_profile(session.user)

        # Program context (if this session is part of a program)
        program_context = None
        if session.program_day:
            program = session.program_day.program
            program_context = {
                'day': session.program_day.day_number,
                'total_days': program.total_days,
                'program_name': program.name,
                'focus_technique': session.program_day.focus_technique,
            }

        prompt = engine.fill_template(variables, profile_context, program_context)
        logger.info('Prompt built for session %s (%d chars)', session_id, len(prompt))
        _save_debug_file(session_id, 'prompt.txt', prompt)

    except Exception as exc:
        logger.exception('Prompt build failed for session %s', session_id)
        _fail_session(session, exc)
        raise self.retry(exc=exc)

    # ── Phase 2: Generate Script (Claude) ─────────────────────────────────
    try:
        ai_service = OpenAIService()
        script = asyncio.run(ai_service.generate_script(prompt))

        audio_service = AudioService()
        clean_script = audio_service.strip_non_spoken_text(script)
        chunks = audio_service.split_text_into_chunks(clean_script)

        _save_debug_file(session_id, 'raw_script.txt', script)
        _save_debug_file(session_id, 'cleaned_script.txt', clean_script)

        session.script_text = script
        session.script_chunks = chunks
        session.status = TherapySession.STATUS_GENERATING_AUDIO
        session.save(update_fields=['script_text', 'script_chunks', 'status'])

        logger.info('Script generated for session %s: %d chunks', session_id, len(chunks))

    except Exception as exc:
        logger.exception('Script generation failed for session %s', session_id)
        _fail_session(session, exc)
        raise self.retry(exc=exc)

    # ── Phase 3: Generate Audio & Music (ElevenLabs) ──────────────────────
    try:
        # 1. Generate Voice
        voice_data = asyncio.run(audio_service.generate_full_audio(script))
        logger.info('Voice generated for session %s: %d bytes', session_id, len(voice_data))
        _save_debug_file(session_id, 'voice_only.mp3', voice_data, mode='wb')

        # 2. Generate Background Music
        music_prompt = "relaxing ambient background music, calming pads, binaural beats, theta waves, peaceful meditation, hypnotherapy, continuous flowing soundscape"
        try:
            music_data = asyncio.run(audio_service.generate_background_music(music_prompt))
            logger.info('Music generated for session %s: %d bytes', session_id, len(music_data))
            _save_debug_file(session_id, 'music_only.mp3', music_data, mode='wb')
        except Exception as e:
            logger.warning('Background music generation failed, continuing with voice only: %s', e)
            music_data = None

        # 3. Mix Voice and Music
        if music_data:
            audio_data = audio_service.mix_audio_with_background(voice_data, music_data, volume_reduction=18)
            logger.info('Audio mixed for session %s: %d bytes', session_id, len(audio_data))
            _save_debug_file(session_id, 'mixed_audio.mp3', audio_data, mode='wb')
        else:
            audio_data = voice_data

    except Exception as exc:
        logger.exception('Audio generation/mixing failed for session %s', session_id)
        _fail_session(session, exc)
        raise self.retry(exc=exc)

    # ── Phase 4: Upload to Storage ────────────────────────────────────────
    # Calculate duration in seconds based on 128 kbps constant bitrate (CBR) MP3 format (16,000 bytes/sec)
    duration_seconds = len(audio_data) // 16000

    try:
        storage = StorageService()
        file_key = f'sessions/{session.user.id}/{session.id}/{uuid.uuid4()}.mp3'
        cdn_url = storage.upload_audio(audio_data, file_key)

        AudioAsset.objects.create(
            session=session,
            file_key=file_key,
            cdn_url=cdn_url,
            file_size_bytes=len(audio_data),
            duration_seconds=duration_seconds,
            format='mp3',
        )
        logger.info('Audio uploaded for session %s: %s', session_id, cdn_url)

    except Exception as exc:
        logger.exception('Storage upload failed for session %s', session_id)
        _fail_session(session, exc)
        raise self.retry(exc=exc)

    # ── Phase 5: Finalise Session ─────────────────────────────────────────
    session.audio_url = cdn_url
    session.audio_duration_seconds = duration_seconds
    session.status = TherapySession.STATUS_COMPLETED
    session.completed_at = timezone.now()
    session.save(update_fields=['audio_url', 'audio_duration_seconds', 'status', 'completed_at'])

    logger.info(
        'Session %s completed successfully in %.1f seconds',
        session_id,
        (session.completed_at - session.created_at).total_seconds(),
    )


def _fail_session(session: TherapySession, exc: Exception):
    """Mark session as failed and refund the user's credits."""
    from apps.credits.services import CreditService

    session.status = TherapySession.STATUS_FAILED
    session.error_message = f'{type(exc).__name__}: {str(exc)}'
    session.save(update_fields=['status', 'error_message'])

    try:
        credit_service = CreditService()
        credit_service.refund_credits(
            session.user,
            session,
            f'Automatic refund: session generation failed ({type(exc).__name__})',
        )
        logger.info('Credits refunded for failed session %s', session.id)
    except Exception as refund_exc:
        logger.error('Credit refund also failed for session %s: %s', session.id, refund_exc)


def _save_debug_file(session_id: int, suffix: str, data, mode: str = 'w'):
    """Helper to save session prompt, scripts, and audio to session_debug/ locally for comparison."""
    import os
    from django.conf import settings
    try:
        debug_dir = settings.BASE_DIR / 'session_debug'
        os.makedirs(debug_dir, exist_ok=True)
        file_path = debug_dir / f'session_{session_id}_{suffix}'
        if mode == 'wb':
            with open(file_path, 'wb') as f:
                f.write(data)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(data))
        logger.info('Saved debug file: %s', file_path)
    except Exception as e:
        logger.error('Failed to save debug file for session %s (suffix: %s): %s', session_id, suffix, e)
