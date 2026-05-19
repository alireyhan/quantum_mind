from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ['*']

# Default to local PostgreSQL; can be overridden via DATABASE_URL
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/quantum_mind')
}


# Allow all origins in dev
CORS_ALLOW_ALL_ORIGINS = True

# Email backend — just print to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable password validators in dev for ease of testing
AUTH_PASSWORD_VALIDATORS = []

# Django Debug Toolbar (optional — install django-debug-toolbar if needed)
INTERNAL_IPS = ['127.0.0.1']

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
