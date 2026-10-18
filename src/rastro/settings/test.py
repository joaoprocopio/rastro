import os

# base.py requires RASTRO_SECRET_KEY when DEBUG is off, and the test run sets neither.
os.environ.setdefault("RASTRO_SECRET_KEY", "secret_key_for_the_test_run")

from rastro.settings.base import *  # noqa: E402, F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

INSTALLED_APPS = INSTALLED_APPS + ["rastro.common.tests.sample"]  # noqa: F405
