from django.db import models
from apps.core.models import TimeStampedModel


class TherapySession(TimeStampedModel):
    """
    Represents a single AI-generated therapy session.
    Created synchronously; generation happens via Celery task.
    """

    STATUS_PENDING = 'pending'
    STATUS_GENERATING_SCRIPT = 'generating_script'
    STATUS_GENERATING_AUDIO = 'generating_audio'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_GENERATING_SCRIPT, 'Generating Script'),
        (STATUS_GENERATING_AUDIO, 'Generating Audio'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='therapy_sessions',
    )
    intake = models.ForeignKey(
        'intake.IntakeResponse',
        on_delete=models.CASCADE,
        related_name='sessions',
    )
    program_day = models.ForeignKey(
        'programs.ProgramDay',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
    )

    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    duration_minutes = models.PositiveIntegerField()
    credits_used = models.PositiveIntegerField()

    # ── Generated Content ─────────────────────────────────────────────────
    script_text = models.TextField(
        blank=True,
        help_text='Full raw script returned by Claude.',
    )
    script_chunks = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of text chunks sent to ElevenLabs TTS.',
    )
    audio_url = models.URLField(
        blank=True,
        help_text='Public CDN URL of the final MP3 file.',
    )
    audio_duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    error_message = models.TextField(
        blank=True,
        help_text='Populated if status=failed.',
    )

    # ── Metadata ──────────────────────────────────────────────────────────
    techniques_used = models.JSONField(
        default=list,
        blank=True,
        help_text='NLP/hypnotherapy techniques auto-selected for this session.',
    )
    problem_category = models.CharField(max_length=50, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Therapy Session'
        verbose_name_plural = 'Therapy Sessions'

    def __str__(self):
        return f'Session {self.id} — {self.user.email} ({self.status})'

    @property
    def is_complete(self):
        return self.status == self.STATUS_COMPLETED

    @property
    def is_failed(self):
        return self.status == self.STATUS_FAILED


class AudioAsset(TimeStampedModel):
    """Stores metadata about the generated MP3 audio file in cloud storage."""

    session = models.OneToOneField(
        TherapySession,
        on_delete=models.CASCADE,
        related_name='audio_asset',
    )
    file_key = models.CharField(
        max_length=500,
        help_text='S3/Spaces object key.',
    )
    cdn_url = models.URLField(help_text='Public CDN URL.')
    file_size_bytes = models.PositiveIntegerField()
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    format = models.CharField(max_length=10, default='mp3')

    class Meta:
        verbose_name = 'Audio Asset'
        verbose_name_plural = 'Audio Assets'

    def __str__(self):
        return f'AudioAsset for Session {self.session_id}'
