from django.db import transaction

from rastro.iam.models import Identity
from rastro.iam.ports import PasswordHasher
from rastro.iam.values import DisplayName, Email, RawPassword


@transaction.atomic
def identity_register(
    *,
    email: Email,
    display_name: DisplayName,
    password: RawPassword,
    password_hasher: PasswordHasher,
) -> None:
    Identity.objects.create(
        email=email,
        display_name=display_name,
        password=password_hasher(password=password).value,
    )
