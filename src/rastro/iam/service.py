from datetime import datetime

import psycopg.errors
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rastro.iam import password
from rastro.iam.exceptions import EmailAlreadyRegisteredError, IncorrectCredentialsError
from rastro.iam.models import Identity, IdentityAuthenticate, IdentityRegister

EMAIL_UNIQUE_CONSTRAINT = "uq_iam_identity_email"


def get(*, db_session: Session, identity_id: int) -> Identity | None:
    return db_session.get(Identity, identity_id)


def get_by_email(*, db_session: Session, email: str) -> Identity | None:
    return db_session.scalar(sa.select(Identity).where(Identity.email == email))


def create(*, db_session: Session, identity_in: IdentityRegister) -> Identity:
    identity = Identity(
        email=identity_in.email,
        password_hash=password.hash_password(identity_in.password.get_secret_value()),
        display_name=identity_in.display_name,
    )

    # The savepoint confines a failed INSERT, so the request transaction stays
    # usable. The unique constraint, not a SELECT beforehand, decides the race
    # between two sign-ups with one email.
    try:
        with db_session.begin_nested():
            db_session.add(identity)
    except IntegrityError as error:
        if _violates(error, EMAIL_UNIQUE_CONSTRAINT):
            raise EmailAlreadyRegisteredError(
                "An identity with this email already exists."
            ) from error
        raise

    # loads `date_joined`, which the database fills in
    db_session.refresh(identity)
    return identity


def authenticate(
    *, db_session: Session, credentials: IdentityAuthenticate, now: datetime
) -> Identity:
    """Return the identity that the credentials belong to.

    An unknown email, a wrong password, and an inactive identity all raise the
    same `IncorrectCredentialsError` after the same amount of hashing work, so
    a caller cannot tell which emails are registered.
    """
    raw_password = credentials.password.get_secret_value()
    identity = get_by_email(db_session=db_session, email=credentials.email)

    if identity is None:
        password.burn_verification(raw_password)
        raise IncorrectCredentialsError("Incorrect email or password.")

    if not password.verify_password(identity.password_hash, raw_password):
        raise IncorrectCredentialsError("Incorrect email or password.")

    if not identity.is_active:
        raise IncorrectCredentialsError("Incorrect email or password.")

    if password.needs_rehash(identity.password_hash):
        identity.password_hash = password.hash_password(raw_password)

    identity.last_login = now
    return identity


def _violates(error: IntegrityError, constraint: str) -> bool:
    cause = error.orig
    return (
        isinstance(cause, psycopg.errors.UniqueViolation)
        and cause.diag.constraint_name == constraint
    )
