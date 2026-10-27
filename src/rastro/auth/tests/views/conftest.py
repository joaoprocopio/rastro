from datetime import timedelta

import pytest
from fastapi import FastAPI

from rastro.auth.domain.ports import Clock, PasswordHasher
from rastro.auth.domain.value_objects import SessionLifetime
from rastro.auth.presentation import dependencies
from rastro.common.presentation.dependencies import app_settings
from rastro.settings import HttpName, SameSite, Settings


@pytest.fixture
def password_hasher() -> PasswordHasher:
    # The app hashes with argon2, so the User of a view test holds an argon2 hash.
    return dependencies.password_hasher()


@pytest.fixture
def clock() -> Clock:
    # The view tests compare expires_at with the wall clock.
    return dependencies.clock()


@pytest.fixture
def other_session_cookie_settings(app: FastAPI, settings: Settings) -> Settings:
    """Settings whose Session cookie differs from the default in every value."""
    other = settings.model_copy(
        update={
            "session_lifetime": SessionLifetime(timedelta(hours=1)),
            "session_cookie_name": HttpName("other_session"),
            "session_cookie_secure": False,
            "session_cookie_httponly": False,
            "session_cookie_samesite": SameSite.STRICT,
        }
    )
    app.dependency_overrides[app_settings] = lambda: other
    return other
