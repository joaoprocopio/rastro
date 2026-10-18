import os

from django.core.wsgi import get_wsgi_application

from rastro import telemetry

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rastro.settings.base")

telemetry.instrument()

application = get_wsgi_application()
