from __future__ import annotations

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

from rastro.common.models import BaseModel
from rastro.common.values import InvalidValueError, StrValueObject
from rastro.iam.fields import DisplayNameField, EmailField
from rastro.iam.values import (
    DISPLAY_NAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    DisplayName,
    Email,
    RawPassword,
)


def _parse[V: StrValueObject](value_object: type[V], value: str | V) -> V:
    if not isinstance(value, str):
        return value
    try:
        return value_object(value)
    except InvalidValueError as error:
        raise ValidationError(str(error), code=error.code) from error


class IdentityManager(BaseUserManager["Identity"]):
    def create_user(
        self,
        *,
        email: str | Email,
        display_name: str | DisplayName,
        password: str | None,
    ) -> Identity:
        # The manager imports the service at call time: the service imports this module.
        from rastro.iam import deps, services

        services.identity_register(
            email=_parse(Email, email),
            display_name=_parse(DisplayName, display_name),
            password=_parse(RawPassword, password or ""),
            password_hasher=deps.PASSWORD_HASHER,
        )
        return self.get(email=email)

    def create_superuser(
        self,
        *,
        email: str | Email,
        display_name: str | DisplayName,
        password: str | None,
    ) -> Identity:
        from rastro.iam import deps, services

        services.identity_register_superuser(
            email=_parse(Email, email),
            display_name=_parse(DisplayName, display_name),
            password=_parse(RawPassword, password or ""),
            password_hasher=deps.PASSWORD_HASHER,
        )
        return self.get(email=email)


class Identity(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = EmailField(max_length=EMAIL_MAX_LENGTH)
    display_name = DisplayNameField(max_length=DISPLAY_NAME_MAX_LENGTH)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = IdentityManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["email"], name="iam_identity_email_unique"),
            models.CheckConstraint(
                condition=models.Q(email=Lower("email")),
                name="iam_identity_email_lowercase",
            ),
        ]

    def __str__(self) -> str:
        return self.email.value
