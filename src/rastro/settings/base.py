from pathlib import Path
from typing import TYPE_CHECKING

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

from rastro.settings.sessions import *  # noqa: F403
from rastro.settings.telemetry import *  # noqa: F403
from rastro_shared_kernel.env import get_env, parse_booleanish, parse_csv

if TYPE_CHECKING:
    import django_stubs_ext

    django_stubs_ext.monkeypatch()


BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = get_env(
    "RASTRO_DEBUG",
    default="0",
    parser=parse_booleanish,
)

_secret_key = get_env("RASTRO_SECRET_KEY")

if _secret_key is None and not DEBUG:
    raise ImproperlyConfigured("Set RASTRO_SECRET_KEY when RASTRO_DEBUG is off.")

SECRET_KEY = _secret_key if _secret_key is not None else get_random_secret_key()

ALLOWED_HOSTS = get_env(
    "RASTRO_ALLOWED_HOSTS",
    default="localhost, 127.0.0.1, 0.0.0.0, [::1]",
    parser=parse_csv,
)

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "rastro.iam",
]

THIRD_PARTY_APPS = [
    "django_extensions",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

DJANGO_MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

LOCAL_MIDDLEWARE = [
    "rastro.middleware.ExceptionHandlerMiddleware",
]

MIDDLEWARE = DJANGO_MIDDLEWARE + LOCAL_MIDDLEWARE

ROOT_URLCONF = "rastro.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "rastro.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env(
            "RASTRO_POSTGRES_DB",
            default="postgres",
        ),
        "USER": get_env(
            "RASTRO_POSTGRES_USER",
            default="postgres",
        ),
        "PASSWORD": get_env(
            "RASTRO_POSTGRES_PASSWORD",
            default="postgres",
        ),
        "HOST": get_env(
            "RASTRO_POSTGRES_HOST",
            default="localhost",
        ),
        "PORT": get_env(
            "RASTRO_POSTGRES_PORT",
            default="5432",
        ),
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher"]
AUTH_PASSWORD_VALIDATORS = []  # type: ignore
AUTH_USER_MODEL = "iam.IdentityModel"

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = False

USE_TZ = True

STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "/static/"

APPEND_SLASH = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} [{name}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "INFO",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console"],
    },
    "loggers": {
        "django": {
            "level": "DEBUG",
            "handlers": [],
            "propagate": True,
        },
        "django.server": {
            "level": "DEBUG",
            "handlers": [],
            "propagate": True,
        },
    },
}
