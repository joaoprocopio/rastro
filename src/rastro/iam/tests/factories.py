from factory.declarations import Sequence
from factory.django import DjangoModelFactory, Password

from rastro.iam.models import Identity
from rastro.iam.values import DisplayName, Email


class IdentityFactory(DjangoModelFactory[Identity]):
    class Meta:
        model = Identity

    email = Sequence(lambda n: Email(f"identity{n}@example.com"))
    display_name = DisplayName("Identity")
    password = Password("password")
