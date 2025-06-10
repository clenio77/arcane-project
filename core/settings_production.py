"""
Configurações de produção para Arcane AI SaaS
"""

from .settings import *
import os
from decouple import config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    'arcane-ai.com',
    'www.arcane-ai.com',
    'api.arcane-ai.com',
    '.herokuapp.com',
    '.vercel.app',
    '.railway.app'
]

# Database para produção
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Cache Redis para produção
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Configurações de segurança
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
    "https://arcane-ai.com",
    "https://www.arcane-ai.com",
    "https://app.arcane-ai.com",
]

CORS_ALLOW_CREDENTIALS = True

# Configurações de email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@arcane-ai.com')

# Configurações de mídia e static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# AWS S3 para arquivos estáticos (opcional)
if config('USE_S3', default=False, cast=bool):
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Configurações de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'oraculo': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'billing': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configurações do Stripe
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET')

# Configurações de rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Configurações de monitoramento
if config('SENTRY_DSN', default=None):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )
    
    sentry_sdk.init(
        dsn=config('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            sentry_logging,
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=config('ENVIRONMENT', default='production')
    )

# Configurações de performance
CONN_MAX_AGE = 60

# Configurações de sessão
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 horas

# Configurações de compressão
COMPRESS_ENABLED = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter',
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]

# Configurações específicas do Arcane AI
ARCANE_AI_VERSION = '2.0.0'
ARCANE_AI_ENVIRONMENT = 'production'

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

# Configurações de backup
BACKUP_ENABLED = True
BACKUP_SCHEDULE = '0 2 * * *'  # Daily at 2 AM
BACKUP_RETENTION_DAYS = 30

# Configurações de analytics
GOOGLE_ANALYTICS_ID = config('GOOGLE_ANALYTICS_ID', default=None)
MIXPANEL_TOKEN = config('MIXPANEL_TOKEN', default=None)

# Configurações de CDN
CDN_URL = config('CDN_URL', default=None)
if CDN_URL:
    STATIC_URL = f'{CDN_URL}/static/'

# Health check
HEALTH_CHECK_ENABLED = True
HEALTH_CHECK_URL = '/health/'

# Feature flags
FEATURE_FLAGS = {
    'advanced_agents': True,
    'hybrid_search': True,
    'personalization': True,
    'auto_improvement': True,
    'multimodal_ai': False,  # Coming soon
    'voice_interface': False,  # Coming soon
}

# Configurações de API
API_RATE_LIMIT = {
    'starter': '100/hour',
    'professional': '1000/hour',
    'enterprise': '10000/hour',
}

# Configurações de webhook
WEBHOOK_TIMEOUT = 30
WEBHOOK_RETRY_ATTEMPTS = 3

# Configurações de queue (Celery)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Configurações de AI
OPENAI_API_KEY = config('OPENAI_API_KEY')
OPENAI_MODEL = config('OPENAI_MODEL', default='gpt-4-turbo-preview')
OPENAI_EMBEDDING_MODEL = config('OPENAI_EMBEDDING_MODEL', default='text-embedding-ada-002')

# Configurações de FAISS
FAISS_INDEX_PATH = config('FAISS_INDEX_PATH', default='/app/data/faiss_index')
FAISS_DIMENSION = config('FAISS_DIMENSION', default=1536, cast=int)

# Configurações de monitoramento de custos
COST_MONITORING_ENABLED = True
COST_ALERT_THRESHOLD = config('COST_ALERT_THRESHOLD', default=1000, cast=float)  # USD

# Configurações de compliance
GDPR_ENABLED = True
LGPD_ENABLED = True
DATA_RETENTION_DAYS = config('DATA_RETENTION_DAYS', default=2555, cast=int)  # 7 anos

# Configurações de multi-tenancy
TENANT_MODEL = 'billing.Organization'
TENANT_DOMAIN_MODEL = 'billing.Organization'
