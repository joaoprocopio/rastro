import os
from pathlib import Path

from pydantic import TypeAdapter

from .schemas import Csv

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    default="i-nh1u%jl!9-f=-kws-k4&z=0z%49e_%m!7dwf=u(c9-wqh)b^",
)

DEBUG = TypeAdapter(bool).validate_strings(os.getenv("DJANGO_DEBUG", default="true"))

ALLOWED_HOSTS = TypeAdapter(Csv).validate_strings(
    os.getenv("DJANGO_ALLOWED_HOSTS", default="localhost, 127.0.0.1, [::1]")
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
    "users",
    "tasks",
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

ROOT_URLCONF = "djangotel.urls"

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

WSGI_APPLICATION = "djangotel.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv(
            "DJANGO_POSTGRES_NAME",
            default="postgres",
        ),
        "USER": os.getenv(
            "DJANGO_POSTGRES_USER",
            default="postgres",
        ),
        "PASSWORD": os.getenv(
            "DJANGO_POSTGRES_PASSWORD",
            default="postgres",
        ),
        "HOST": os.getenv(
            "DJANGO_POSTGRES_HOST",
            default="localhost",
        ),
        "PORT": os.getenv(
            "DJANGO_POSTGRES_PORT",
            default="5432",
        ),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"
