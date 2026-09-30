"""Server-side sessions, after the OWASP Session Management Cheat Sheet.

The session token is 256 bits from `secrets`, lives in an `HttpOnly` cookie,
and changes on every sign-in. The server ends a session after
`session_idle_timeout` without a request, or `session_absolute_timeout` after
the sign-in, whichever comes first.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Annotated, Final

import sqlalchemy as sa
from fastapi import Depends, Security
from fastapi.security import APIKeyCookie
from sqlalchemy.orm import Session, joinedload

from rastro.config import Settings, SettingsDep
from rastro.database.core import DbSession
from rastro.iam.exceptions import NotAuthenticatedError
from rastro.iam.models import Identity
from rastro.iam.session.models import IdentitySession
from rastro.security import SESSION_COOKIE_NAME
from rastro.utils import utcnow

# A request refreshes `last_seen_at` at most once per interval, so a busy
# session costs one UPDATE per minute in place of one per request.
TOUCH_INTERVAL: Final = timedelta(minutes=1)

session_cookie = APIKeyCookie(
    name=SESSION_COOKIE_NAME,
    auto_error=False,
    description="Session token, set by `POST /api/v1/iam/session`.",
)
SessionToken = Annotated[str | None, Security(session_cookie)]


def _digest(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


def _is_expired(session: IdentitySession, *, now: datetime, settings: Settings) -> bool:
    return (
        session.expires_at <= now
        or session.last_seen_at + settings.session_idle_timeout <= now
    )


def start(
    *, db_session: Session, identity: Identity, now: datetime, settings: Settings
) -> str:
    """Start a session for `identity` and return its token, the cookie value."""
    # Each sign-in removes the identity's expired sessions, so the table keeps
    # no more stale rows per identity than it has live ones.
    db_session.execute(
        sa.delete(IdentitySession).where(
            IdentitySession.identity_id == identity.id,
            sa.or_(
                IdentitySession.expires_at <= now,
                IdentitySession.last_seen_at <= now - settings.session_idle_timeout,
            ),
        )
    )

    token = secrets.token_urlsafe(32)
    db_session.add(
        IdentitySession(
            token_digest=_digest(token),
            identity=identity,
            created_at=now,
            last_seen_at=now,
            expires_at=now + settings.session_absolute_timeout,
        )
    )
    db_session.flush()
    return token


def end(*, db_session: Session, token: str) -> None:
    db_session.execute(
        sa.delete(IdentitySession).where(IdentitySession.token_digest == _digest(token))
    )


def resolve(
    *, db_session: Session, token: str, now: datetime, settings: Settings
) -> Identity | None:
    """Return the identity of a live session, or `None`."""
    session = db_session.scalar(
        sa.select(IdentitySession)
        .options(joinedload(IdentitySession.identity))
        .where(IdentitySession.token_digest == _digest(token))
    )

    if session is None or _is_expired(session, now=now, settings=settings):
        return None

    if not session.identity.is_active:
        return None

    if now - session.last_seen_at >= TOUCH_INTERVAL:
        session.last_seen_at = now

    return session.identity


def get_current_identity(
    db_session: DbSession, settings: SettingsDep, token: SessionToken
) -> Identity:
    if token is None:
        raise NotAuthenticatedError("No session cookie.")

    identity = resolve(
        db_session=db_session, token=token, now=utcnow(), settings=settings
    )

    if identity is None:
        raise NotAuthenticatedError("The session is invalid or has expired.")

    return identity


CurrentIdentity = Annotated[Identity, Depends(get_current_identity)]
