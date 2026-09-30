from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Response
from sqlalchemy.orm import Session

from rastro.config import Settings, SettingsDep
from rastro.database.core import DbSession
from rastro.iam import service
from rastro.iam.models import (
    Identity,
    IdentityAuthenticate,
    IdentityRead,
    IdentityRegister,
)
from rastro.iam.session import service as session_service
from rastro.iam.session.service import CurrentIdentity, SessionToken
from rastro.security import (
    SESSION_COOKIE_NAME,
    delete_cookie,
    set_cookie,
    set_csrf_cookie,
)
from rastro.utils import utcnow

router = APIRouter()


def _start_session(
    *,
    response: Response,
    db_session: Session,
    settings: Settings,
    identity: Identity,
    previous_token: str | None,
    now: datetime,
) -> None:
    # A new token on every sign-in defeats session fixation: a token that an
    # attacker planted before the sign-in never becomes authenticated.
    if previous_token is not None:
        session_service.end(db_session=db_session, token=previous_token)

    token = session_service.start(
        db_session=db_session, identity=identity, now=now, settings=settings
    )
    set_cookie(
        response,
        key=SESSION_COOKIE_NAME,
        value=token,
        secure=settings.cookie_secure,
        httponly=True,
    )
    set_csrf_cookie(
        response,
        secret=settings.secret_key.get_secret_value().encode(),
        session_token=token,
        secure=settings.cookie_secure,
    )


@router.post("/identities", status_code=HTTPStatus.CREATED)
def register_identity(
    identity_in: IdentityRegister,
    response: Response,
    db_session: DbSession,
    settings: SettingsDep,
    previous_token: SessionToken,
) -> IdentityRead:
    """Register a new identity and sign it in."""
    identity = service.create(db_session=db_session, identity_in=identity_in)
    _start_session(
        response=response,
        db_session=db_session,
        settings=settings,
        identity=identity,
        previous_token=previous_token,
        now=utcnow(),
    )
    return IdentityRead.model_validate(identity)


@router.post("/session")
def authenticate(
    credentials: IdentityAuthenticate,
    response: Response,
    db_session: DbSession,
    settings: SettingsDep,
    previous_token: SessionToken,
) -> IdentityRead:
    """Start a session from an email and a password."""
    now = utcnow()
    identity = service.authenticate(
        db_session=db_session, credentials=credentials, now=now
    )
    _start_session(
        response=response,
        db_session=db_session,
        settings=settings,
        identity=identity,
        previous_token=previous_token,
        now=now,
    )
    return IdentityRead.model_validate(identity)


@router.get("/session")
def get_session(identity: CurrentIdentity) -> IdentityRead:
    """Return the identity of the current session."""
    return IdentityRead.model_validate(identity)


@router.delete("/session", status_code=HTTPStatus.NO_CONTENT)
def end_session(
    response: Response,
    db_session: DbSession,
    settings: SettingsDep,
    token: SessionToken,
) -> None:
    """End the current session. Without a session, the request does nothing."""
    if token is not None:
        session_service.end(db_session=db_session, token=token)

    delete_cookie(
        response, key=SESSION_COOKIE_NAME, secure=settings.cookie_secure, httponly=True
    )
    set_csrf_cookie(
        response,
        secret=settings.secret_key.get_secret_value().encode(),
        session_token=None,
        secure=settings.cookie_secure,
    )


@router.get("/csrftoken", status_code=HTTPStatus.NO_CONTENT)
def issue_csrf_token(
    response: Response, settings: SettingsDep, token: SessionToken
) -> None:
    """Set the `csrftoken` cookie that unsafe requests echo in `X-CSRFToken`."""
    set_csrf_cookie(
        response,
        secret=settings.secret_key.get_secret_value().encode(),
        session_token=token,
        secure=settings.cookie_secure,
    )
