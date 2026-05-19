from django.apps import AppConfig

class SessionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sessions'
    label = 'therapy_sessions'  # Avoid collision with django.contrib.sessions
