from __future__ import annotations

from typing import Any, cast

from django.contrib import auth
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Permission,
    PermissionsMixin,
)
from django.db import models
from django.db.models import QuerySet
from django.db.models.base import Model
from django.utils import timezone


class IdentityManager(BaseUserManager["IdentityModel"]):
    use_in_migrations = True

    def _create_user_object(
        self,
        display_name: str,
        email: str,
        password: str,
        **extra_fields: Any,
    ) -> IdentityModel:
        email = self.normalize_email(email)
        user = self.model(display_name=display_name, email=email, **extra_fields)
        user.password = make_password(password)
        return user

    def _create_user(
        self,
        display_name: str,
        email: str,
        password: str,
        **extra_fields: Any,
    ) -> IdentityModel:
        user = self._create_user_object(display_name, email, password, **extra_fields)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        display_name: str,
        email: str,
        password: str,
        **extra_fields: Any,
    ) -> IdentityModel:
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(display_name, email, password, **extra_fields)

    setattr(create_user, "alters_data", True)

    def create_superuser(
        self,
        display_name: str,
        email: str,
        password: str,
        **extra_fields: Any,
    ) -> IdentityModel:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(display_name, email, password, **extra_fields)

    setattr(create_superuser, "alters_data", True)

    def with_perm(
        self,
        perm: str | Permission,
        is_active: bool = True,
        include_superusers: bool = True,
        backend: Any = None,
        obj: Model | None = None,
    ) -> QuerySet[IdentityModel]:
        if backend is None:
            backends = auth.get_backends()
            if len(backends) == 1:
                backend = backends[0]
            else:
                raise ValueError(
                    "You have multiple authentication backends configured and "
                    "therefore must provide the `backend` argument."
                )
        elif not isinstance(backend, str):
            raise TypeError(
                "backend must be a dotted import path string (got %r)." % backend
            )
        else:
            backend = auth.load_backend(backend)

        if hasattr(backend, "with_perm"):
            return cast(
                QuerySet[IdentityModel],
                backend.with_perm(
                    perm,
                    is_active=is_active,
                    include_superusers=include_superusers,
                    obj=obj,
                ),
            )

        return self.none()


# https://docs.djangoproject.com/en/6.0/topics/auth/customizing/
class IdentityModel(AbstractBaseUser, PermissionsMixin):
    display_name = models.CharField(max_length=320)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = IdentityManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
