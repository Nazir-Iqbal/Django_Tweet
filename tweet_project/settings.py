import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-change-me')
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1')
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'chat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tweet_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tweet_project.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

AUTH_USER_MODEL = 'accounts.User'

# LLM Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

LLM_MODELS = {
    "openai": ["GPT-5", "GPT-5 Mini", "GPT-4.1", "GPT-4.1 Mini", "GPT-4o", "GPT-4o Mini", "GPT-4 Turbo", "GPT-4"],
    "claude": ["Claude Opus-4.5", "Claude Sonnet-4.5", "Claude Haiku-4.5", "Claude Sonnet-4", "Claude Opus-4", "Claude Opus-4.1"],
    "gemini": ["Gemini-3 Pro", "Gemini-2.5 Pro", "Gemini-2.5 Flash"],
}

LLM_MODEL_MAP = {
    "GPT-5": "gpt-5",
    "GPT-5 Mini": "gpt-5-mini",
    "GPT-4.1": "gpt-4.1",
    "GPT-4.1 Mini": "gpt-4.1-mini",
    "GPT-4o": "gpt-4o",
    "GPT-4o Mini": "gpt-4o-mini",
    "GPT-4 Turbo": "gpt-4-turbo",
    "GPT-4": "gpt-4",
    "Claude Opus-4.5": "claude-opus-4-5-20250414",
    "Claude Sonnet-4.5": "claude-sonnet-4-5-20250414",
    "Claude Haiku-4.5": "claude-haiku-4-5-20250414",
    "Claude Sonnet-4": "claude-sonnet-4-20250514",
    "Claude Opus-4": "claude-opus-4-20250514",
    "Claude Opus-4.1": "claude-opus-4-1-20250618",
    "Gemini-3 Pro": "gemini-3-pro",
    "Gemini-2.5 Pro": "gemini-2.5-pro",
    "Gemini-2.5 Flash": "gemini-2.5-flash",
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
