from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the username field."""

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # ── Demographics ───────────────────────────────────────────────────────
    age = models.PositiveIntegerField(null=True, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    pronouns = models.CharField(max_length=20, blank=True)

    # ── Credit System ──────────────────────────────────────────────────────
    free_minutes_used = models.PositiveIntegerField(
        default=0,
        help_text='Minutes consumed from the free tier allocation.'
    )
    purchased_credits = models.PositiveIntegerField(
        default=0,
        help_text='Purchased credit minutes available for sessions.'
    )

    # ── Subscription ───────────────────────────────────────────────────────
    is_premium = models.BooleanField(default=False)
    premium_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the premium subscription lapses. Null = no active sub.'
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email
