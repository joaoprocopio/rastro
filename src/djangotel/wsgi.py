import os

from django.core.wsgi import get_wsgi_application

from djangotel import telemetry

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangotel.settings")

telemetry.instrument_django_wsgi_telemetry()

application = get_wsgi_application()
