import pytest
from django.contrib.auth.models import AnonymousUser
from model_bakery import baker

from rastro.conta.models import Conta


@pytest.fixture
def conta(db: None) -> Conta:
    name = "user"
    email = f"{name}@example.com"
    password = "password"

    try:
        conta = Conta.objects.get(email=email)
    except Conta.DoesNotExist:
        conta = baker.make(
            Conta,
            display_name=name,
            email=email,
        )
        conta.set_password(password)
        conta.save()

    return conta


@pytest.fixture
def anonymous_user(db: None) -> AnonymousUser:
    return AnonymousUser()
