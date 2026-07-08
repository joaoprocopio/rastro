from pathlib import Path
from typing import TYPE_CHECKING

from rastro_shared_kernel.env import get_env, parse_booleanish, parse_csv

if TYPE_CHECKING:
    import django_stubs_ext

    django_stubs_ext.monkeypatch()


BASE_DIR = Path(__file__).resolve().parent.parent

SERVICE_NAMESPACE = get_env(
    "RASTRO_DJANGO_SERVICE_NAMESPACE",
    default="rastro",
)

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
    "rastro.conta",
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
AUTH_USER_MODEL = "conta.Conta"

CSRF_COOKIE_DOMAIN = get_env(
    "RASTRO_DJANGO_CSRF_COOKIE_DOMAIN",
    default=".localhost",
)
CSRF_TRUSTED_ORIGINS = get_env(
    "RASTRO_DJANGO_CSRF_TRUSTED_ORIGINS",
    default="http://localhost:8000",
    parser=parse_csv,
)
CSRF_COOKIE_HTTPONLY = False


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = False

USE_TZ = True


STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "/static/"

APPEND_SLASH = False


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
