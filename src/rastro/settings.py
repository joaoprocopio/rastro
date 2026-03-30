from pathlib import Path

import django_stubs_ext

from rastro.env import get_env, parse_booleanish, parse_csv

django_stubs_ext.monkeypatch()

BASE_DIR = Path(__file__).resolve().parent.parent

SERVICE_NAME = get_env(
    "RASTRO_DJANGO_SERVICE_NAME",
    default="rastro",
)

DEPLOYMENT_ID = get_env(
    "RASTRO_DJANGO_DEPLOYMENT_ID",
    default="2f92ca37",
)

DEPLOYMENT_ENVIRONMENT = get_env(
    "RASTRO_DJANGO_DEPLOYMENT_ENVIRONMENT",
    default="dev",
)

SECRET_KEY = get_env(
    "RASTRO_DJANGO_SECRET_KEY",
    default="i-nh1u%jl!9-f=-kws-k4&z=0z%49e_%m!7dwf=u(c9-wqh)b^",
)

DEBUG = get_env(
    "RASTRO_DJANGO_DEBUG",
    default="1",
    parser=parse_booleanish,
)


ALLOWED_HOSTS = get_env(
    "RASTRO_DJANGO_ALLOWED_HOSTS",
    default="localhost, 127.0.0.1, [::1]",
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
    "rastro.auth",
    "rastro.tasks",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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
            "RASTRO_DJANGO_POSTGRES_DB",
            default="postgres",
        ),
        "USER": get_env(
            "RASTRO_DJANGO_POSTGRES_USER",
            default="postgres",
        ),
        "PASSWORD": get_env(
            "RASTRO_DJANGO_POSTGRES_PASSWORD",
            default="postgres",
        ),
        "HOST": get_env(
            "RASTRO_DJANGO_POSTGRES_HOST",
            default="localhost",
        ),
        "PORT": get_env(
            "RASTRO_DJANGO_POSTGRES_PORT",
            default="5432",
        ),
    }
}


CSRF_COOKIE_HTTPONLY = True


PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher"]
AUTH_PASSWORD_VALIDATORS = []  # type: ignore


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"

OTEL_GRPC_ENDPOINT = get_env(
    "RASTRO_DJANGO_OTEL_GRPC_ENDPOINT",
    default="localhost:4317",
)
OTEL_HTTP_ENDPOINT = get_env(
    "RASTRO_DJANGO_OTEL_HTTP_ENDPOINT",
    default="localhost:4318",
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.db.backends": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
    },
}
