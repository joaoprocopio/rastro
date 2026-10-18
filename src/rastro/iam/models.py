from __future__ import annotations

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.db.models.functions import Lower

from rastro.common.fields import StrValueObjectField, parse_value_object
from rastro.common.models import BaseModel
from rastro.iam.values import (
    DISPLAY_NAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    DisplayName,
    Email,
    RawPassword,
)


class EmailValueField(StrValueObjectField[Email]):
    value_object = Email


class DisplayNameValueField(StrValueObjectField[DisplayName]):
    value_object = DisplayName


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
            email=parse_value_object(Email, email),
            display_name=parse_value_object(DisplayName, display_name),
            password=parse_value_object(RawPassword, password or ""),
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
            email=parse_value_object(Email, email),
            display_name=parse_value_object(DisplayName, display_name),
            password=parse_value_object(RawPassword, password or ""),
            password_hasher=deps.PASSWORD_HASHER,
        )
        return self.get(email=email)


class Identity(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = EmailValueField(max_length=EMAIL_MAX_LENGTH)
    display_name = DisplayNameValueField(max_length=DISPLAY_NAME_MAX_LENGTH)
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
