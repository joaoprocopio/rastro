import os

from django.core.asgi import get_asgi_application

from rastro import telemetry

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rastro.settings.base")

telemetry.instrument()

application = get_asgi_application()
