from rastro.common.env import get_env, parse_csv

CSRF_COOKIE_DOMAIN = get_env(
    "RASTRO_CSRF_COOKIE_DOMAIN",
    default=".localhost",
)

CSRF_TRUSTED_ORIGINS = get_env(
    "RASTRO_CSRF_TRUSTED_ORIGINS",
    default="http://localhost:8000",
    parser=parse_csv,
)

# The single-page app reads the token from the cookie and sends it in X-CSRFToken.
CSRF_COOKIE_HTTPONLY = False

CSRF_FAILURE_VIEW = "rastro.common.views.csrf_failure_view"
