from __future__ import annotations

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.db.models.functions import Lower

from rastro.common.fields import ValueObjectField, django_validation_errors
from rastro.common.models import BaseModel
from rastro.iam.values import (
    DISPLAY_NAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    DisplayName,
    Email,
    RawPassword,
)


class EmailValueField(ValueObjectField[Email]):
    value_object = Email


class DisplayNameValueField(ValueObjectField[DisplayName]):
    value_object = DisplayName


def _parse_registration(
    *,
    email: str | Email,
    display_name: str | DisplayName,
    password: str | None,
) -> tuple[Email, DisplayName, RawPassword]:
    with django_validation_errors():
        return (
            Email.model_validate(email),
            DisplayName.model_validate(display_name),
            RawPassword.model_validate(password or ""),
        )


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

        parsed_email, parsed_display_name, parsed_password = _parse_registration(
            email=email, display_name=display_name, password=password
        )
        services.identity_register(
            email=parsed_email,
            display_name=parsed_display_name,
            password=parsed_password,
            password_hasher=deps.PASSWORD_HASHER,
        )
        return self.get(email=parsed_email)

    def create_superuser(
        self,
        *,
        email: str | Email,
        display_name: str | DisplayName,
        password: str | None,
    ) -> Identity:
        from rastro.iam import deps, services

        parsed_email, parsed_display_name, parsed_password = _parse_registration(
            email=email, display_name=display_name, password=password
        )
        services.identity_register_superuser(
            email=parsed_email,
            display_name=parsed_display_name,
            password=parsed_password,
            password_hasher=deps.PASSWORD_HASHER,
        )
        return self.get(email=parsed_email)


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
        return self.email.root
