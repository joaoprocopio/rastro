import pytest
from django.contrib.auth.models import AnonymousUser
from model_bakery import baker

from rastro.iam.models import IdentityModel


@pytest.fixture
def identity(db: None) -> IdentityModel:
    name = "user"
    email = f"{name}@example.com"
    password = "password"

    try:
        identity = IdentityModel.objects.get(email=email)
    except IdentityModel.DoesNotExist:
        identity = baker.make(
            IdentityModel,
            display_name=name,
            email=email,
        )
        identity.set_password(password)
        identity.save()

    return identity


@pytest.fixture
def anonymous_user(db: None) -> AnonymousUser:
    return AnonymousUser()
