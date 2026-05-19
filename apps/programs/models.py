from django.db import models
from apps.core.models import TimeStampedModel


class TherapyProgram(TimeStampedModel):
    """A multi-day structured therapy program (e.g. "21-Day Sleep Reset")."""

    name = models.CharField(max_length=200)
    description = models.TextField()
    total_days = models.PositiveIntegerField()
    category = models.CharField(
        max_length=50,
        help_text='Problem category this program targets (sleep, anxiety, etc.)',
    )
    is_active = models.BooleanField(default=True)
    is_premium_only = models.BooleanField(default=False)
    thumbnail_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Therapy Program'
        verbose_name_plural = 'Therapy Programs'

    def __str__(self):
        return f'{self.name} ({self.total_days} days)'


class ProgramDay(TimeStampedModel):
    """
    A single day within a therapy program.
    Referenced by TherapySession to inject program context into the Claude prompt.
    """

    program = models.ForeignKey(
        TherapyProgram,
        on_delete=models.CASCADE,
        related_name='days',
    )
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    focus_technique = models.CharField(
        max_length=100,
        blank=True,
        help_text='Primary therapeutic technique for this day.',
    )

    class Meta:
        ordering = ['program', 'day_number']
        unique_together = ['program', 'day_number']
        verbose_name = 'Program Day'
        verbose_name_plural = 'Program Days'

    def __str__(self):
        return f'{self.program.name} — Day {self.day_number}: {self.title}'


class UserProgramEnrollment(TimeStampedModel):
    """Tracks a user's progress through a multi-day program."""

    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_PAUSED = 'paused'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_PAUSED, 'Paused'),
    ]

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='program_enrollments',
    )
    program = models.ForeignKey(
        TherapyProgram,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    current_day = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'program']
        ordering = ['-created_at']
        verbose_name = 'User Program Enrollment'
        verbose_name_plural = 'User Program Enrollments'

    def __str__(self):
        return f'{self.user.email} → {self.program.name} (Day {self.current_day}/{self.program.total_days})'

    @property
    def progress_percentage(self):
        return round((self.current_day / self.program.total_days) * 100)

    def get_current_program_day(self):
        return self.program.days.filter(day_number=self.current_day).first()
