from django.db import models
from apps.core.models import TimeStampedModel


class MoodEntry(TimeStampedModel):
    """Tracks mood before and after a therapy session on a 1-10 scale."""

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='mood_entries',
    )
    session = models.ForeignKey(
        'therapy_sessions.TherapySession',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='mood_entries',
    )
    mood_before = models.PositiveSmallIntegerField(
        help_text='Mood score before the session (1-10).'
    )
    mood_after = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='Mood score after the session (1-10). Filled in post-session.',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mood Entry'
        verbose_name_plural = 'Mood Entries'

    def __str__(self):
        return f'{self.user.email} — before:{self.mood_before} after:{self.mood_after}'

    @property
    def improvement(self):
        if self.mood_after is not None:
            return self.mood_after - self.mood_before
        return None


class SessionFeedback(TimeStampedModel):
    """Post-session structured feedback used by the adaptive AI system."""

    session = models.OneToOneField(
        'therapy_sessions.TherapySession',
        on_delete=models.CASCADE,
        related_name='feedback',
    )
    effectiveness_rating = models.PositiveSmallIntegerField(
        help_text='Overall effectiveness rating (1-5).'
    )
    techniques_resonated = models.JSONField(
        default=list,
        blank=True,
        help_text='List of technique names the user found particularly effective.',
    )
    techniques_to_adjust = models.JSONField(
        default=list,
        blank=True,
        help_text='Techniques the user wants de-emphasised in future sessions.',
    )
    general_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Session Feedback'
        verbose_name_plural = 'Session Feedback'

    def __str__(self):
        return f'Feedback for Session {self.session_id} — {self.effectiveness_rating}/5'


class TherapeuticProfile(TimeStampedModel):
    """
    Aggregated adaptive AI profile per user.
    Rebuilt after every session feedback submission.
    Injected into the Claude prompt as "Returning User Context".
    """

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='therapeutic_profile',
    )
    most_effective_techniques = models.JSONField(
        default=list,
        help_text='Techniques consistently rated highly by this user.',
    )
    least_effective_techniques = models.JSONField(
        default=list,
        help_text='Techniques to de-emphasise.',
    )
    average_mood_improvement_by_category = models.JSONField(
        default=dict,
        help_text='Average mood delta grouped by problem_category.',
    )
    session_count = models.PositiveIntegerField(default=0)
    key_themes = models.JSONField(
        default=list,
        help_text='Recurring themes extracted from feedback notes.',
    )

    class Meta:
        verbose_name = 'Therapeutic Profile'
        verbose_name_plural = 'Therapeutic Profiles'

    def __str__(self):
        return f'TherapeuticProfile for {self.user.email} ({self.session_count} sessions)'
