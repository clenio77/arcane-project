"""
Configurações específicas para Heroku
"""

import os
from decouple import config
from .settings import *

# Importar dj_database_url apenas se disponível
try:
    import dj_database_url
    HAS_DJ_DATABASE_URL = True
except ImportError:
    HAS_DJ_DATABASE_URL = False

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Heroku automatically provides PORT
PORT = int(os.environ.get('PORT', 8000))

# Allowed hosts para Heroku
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.herokuapp.com',
    config('DOMAIN_NAME', default='arcane-ai.herokuapp.com'),
]

# Database configuration para Heroku
if HAS_DJ_DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL', default='sqlite:///db.sqlite3'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Fallback para desenvolvimento local
    DATABASE_URL = config('DATABASE_URL', default='sqlite:///db.sqlite3')
    if DATABASE_URL.startswith('postgres://'):
        # Parse manual da URL do PostgreSQL
        import urllib.parse as urlparse
        url = urlparse.urlparse(DATABASE_URL)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': url.path[1:],
                'USER': url.username,
                'PASSWORD': url.password,
                'HOST': url.hostname,
                'PORT': url.port,
                'OPTIONS': {
                    'sslmode': 'require',
                },
            }
        }
    else:
        # SQLite para desenvolvimento
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }

# Redis configuration para Heroku
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

# Celery configuration para Heroku
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Static files configuration para Heroku
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Whitenoise para servir arquivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Adicionar Whitenoise
] + MIDDLEWARE[1:]  # Manter o resto do middleware

# Media files para Heroku (usar S3 em produção)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações de segurança para produção
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# CORS para API
CORS_ALLOWED_ORIGINS = [
    f"https://{config('DOMAIN_NAME', default='arcane-ai.herokuapp.com')}",
    "http://localhost:3000",  # Para desenvolvimento frontend
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@arcane-ai.com')

# Configurações de logging para Heroku
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'oraculo': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'billing': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configurações do Stripe
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Configurações de IA
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
OPENAI_MODEL = config('OPENAI_MODEL', default='gpt-4-turbo-preview')
OPENAI_EMBEDDING_MODEL = config('OPENAI_EMBEDDING_MODEL', default='text-embedding-ada-002')

# Configurações de FAISS para Heroku
FAISS_INDEX_PATH = os.path.join(BASE_DIR, 'data', 'faiss_index')
FAISS_DIMENSION = config('FAISS_DIMENSION', default=1536, cast=int)

# Criar diretórios necessários
os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Configurações específicas do Heroku
HEROKU_APP_NAME = config('HEROKU_APP_NAME', default='arcane-ai')

# Configurações de rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Configurações de monitoramento (Sentry)
SENTRY_DSN = config('SENTRY_DSN', default=None)
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            sentry_logging,
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment='heroku'
    )

# Configurações de performance
CONN_MAX_AGE = 60

# Configurações de sessão
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 horas

# Feature flags para Heroku
FEATURE_FLAGS = {
    'advanced_agents': True,
    'hybrid_search': True,
    'personalization': True,
    'auto_improvement': True,
    'billing_system': True,
    'api_access': True,
}

# Configurações de backup (desabilitado no Heroku)
BACKUP_ENABLED = False

# Configurações específicas do Arcane AI
ARCANE_AI_VERSION = '2.0.0'
ARCANE_AI_ENVIRONMENT = 'heroku'

# Limites de uso por plano
PLAN_LIMITS = {
    'starter': {
        'queries_per_month': 1000,
        'max_users': 5,
        'max_storage_gb': 10,
        'max_agents': 1,
    },
    'professional': {
        'queries_per_month': 10000,
        'max_users': 25,
        'max_storage_gb': 100,
        'max_agents': 3,
    },
    'enterprise': {
        'queries_per_month': -1,  # Unlimited
        'max_users': -1,  # Unlimited
        'max_storage_gb': -1,  # Unlimited
        'max_agents': -1,  # Unlimited
    }
}
