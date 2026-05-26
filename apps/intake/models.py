from django.db import models
from apps.core.models import TimeStampedModel



class IntakeResponse(TimeStampedModel):
    """
    Stores the complete clinical intake wizard response for a user session.
    Each field maps directly to a {{variable}} in the hypnotherapy prompt template.
    """

    REPRESENTATIONAL_SYSTEM_CHOICES = [
        ('visual', 'Visual'),
        ('auditory', 'Auditory'),
        ('kinesthetic', 'Kinesthetic'),
    ]

    POST_SESSION_STATE_CHOICES = [
        ('sleep', 'Drift to sleep'),
        ('alert', 'Wake alert'),
    ]

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='intakes',
    )

    # ── STEP 1: What Brings You Here ─────────────────────────────────────
    main_issue = models.TextField(
        blank=True,
        default='',
        help_text='The primary problem the user wants to address.'
    )
    issue_duration = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='How long this issue has persisted, e.g. "6 months", "10 years".'
    )

    # ── STEP 2: Triggers & Emotions ───────────────────────────────────────
    triggers = models.JSONField(
        default=list,
        blank=True,
        help_text='Situations or stimuli that trigger the problem. Stored as list of strings.',
    )
    symptoms = models.JSONField(
        default=list,
        blank=True,
        help_text='Emotions and physical sensations experienced (labeled "emotions" in UI).',
    )

    # ── STEP 3: The Shift ─────────────────────────────────────────────────
    behavior_to_change = models.TextField(
        blank=True,
        default='',
        help_text='The specific behaviour the user wants to modify.'
    )
    desired_emotional_shift = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='The emotional state the user wants to move toward.',
    )

    # ── STEP 4: Your Vision ───────────────────────────────────────────────
    success_vision = models.TextField(
        blank=True,
        default='',
        help_text='The user\'s own description of life after the transformation.'
    )
    positive_anchoring_memory = models.TextField(
        blank=True,
        default='',
        help_text='A real positive memory used for NLP resource anchoring.'
    )

    # ── STEP 5: Your World ────────────────────────────────────────────────
    interests = models.JSONField(
        default=list,
        blank=True,
        help_text='Hobbies/interests used to build personalised metaphors. Stored as list of strings.',
    )
    work_life_environment = models.TextField(
        blank=True,
        default='',
        help_text='Description of the user\'s daily work and life context.'
    )

    # ── STEP 6: Inner Dialogue (Advanced) ────────────────────────────────
    repeating_thoughts = models.TextField(
        blank=True,
        help_text='Recurring negative thought patterns.',
    )
    negative_beliefs = models.TextField(
        blank=True,
        help_text='Core limiting beliefs identified by the user.',
    )
    has_inner_conflict = models.BooleanField(
        null=True,
        blank=True,
        help_text='Whether the user experiences conflicting motivations.',
    )
    inner_conflict_description = models.TextField(
        blank=True,
        help_text='Description of the inner conflict — enables Parts Therapy.',
    )

    # ── STEP 7: Body & Mind (Advanced) ───────────────────────────────────
    resistance_protection = models.TextField(
        blank=True,
        help_text='What the resistant part is protecting the user against.',
    )
    body_location = models.CharField(
        max_length=100,
        blank=True,
        help_text='Where in the body the emotion is felt — enables Somatic Release.',
    )
    representational_system = models.CharField(
        max_length=20,
        choices=REPRESENTATIONAL_SYSTEM_CHOICES,
        blank=True,
        help_text='Primary NLP sensory channel — determines language style of suggestions.',
    )

    # ── STEP 8: Deeper Patterns (Advanced) ───────────────────────────────
    fears_about_change = models.TextField(
        blank=True,
        help_text='What the user fears might happen if they change.',
    )
    connected_to_past_event = models.BooleanField(
        null=True,
        blank=True,
        help_text='Whether the issue connects to a past event — enables Timeline Therapy.',
    )
    key_affirmations = models.JSONField(
        default=list,
        blank=True,
        help_text='User-supplied affirmations for identity-level installation. Stored as list of strings.',
    )
    language_to_avoid = models.JSONField(
        default=list,
        blank=True,
        help_text='Words or phrases the AI must not use (trauma-sensitive care). Stored as list of strings.',
    )

    # ── STEP 9: Session Preferences ──────────────────────────────────────
    session_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Requested session length in minutes (10-45).',
    )
    focus_category = models.CharField(
        max_length=100,
        blank=True,
        help_text='Optional override for focus area.',
    )
    post_session_state = models.CharField(
        max_length=20,
        choices=POST_SESSION_STATE_CHOICES,
        default='alert',
        help_text='Whether session ends with sleep induction or alert emergence.',
    )

    # ── COMPUTED (auto-diagnosed) ─────────────────────────────────────────
    problem_category = models.CharField(
        max_length=50,
        blank=True,
        help_text='Auto-diagnosed problem category (sleep, anxiety, trauma, etc.).',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Intake Response'
        verbose_name_plural = 'Intake Responses'

    def __str__(self):
        issue_text = self.main_issue or ''
        return f'{self.user.email} — {issue_text[:60]} ({self.created_at.date()})'
