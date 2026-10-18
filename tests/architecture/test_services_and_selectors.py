from typing import Protocol

from django.contrib.auth.hashers import make_password
from django.http import HttpRequest

from rastro.iam.values import Email
from tests.architecture.helpers import module_with
from tests.architecture.rules import (
    Role,
    django_conf_imports,
    logic_modules,
    module_source,
    signature_violations,
)

SERVICES_MODULE = f"tests.sample.{Role.SERVICES}"
SELECTORS_MODULE = f"tests.sample.{Role.SELECTORS}"


class Hasher(Protocol):
    def __call__(self, *, password: str) -> str: ...


def test_every_service_and_selector_follows_the_signature_rules() -> None:
    violations = [
        violation
        for role in Role
        for module in logic_modules(role)
        for violation in signature_violations(module, role)
    ]

    assert violations == []


def test_no_service_or_selector_imports_django_conf() -> None:
    imports = [
        line
        for role in Role
        for module in logic_modules(role)
        for line in django_conf_imports(
            source=module_source(module), name=module.__name__
        )
    ]

    assert imports == []


def test_a_service_that_follows_every_rule_passes() -> None:
    def identity_register(*, email: Email, hasher: Hasher) -> None:
        pass

    def session_start(*, request: HttpRequest, email: Email) -> None:
        pass

    module = module_with(SERVICES_MODULE, identity_register, session_start)

    assert signature_violations(module, Role.SERVICES) == []


def test_a_selector_that_returns_data_passes() -> None:
    def identity_get_current(*, request: HttpRequest) -> Email:
        return Email("person@example.com")

    def identity_list_by_email(*, email: Email) -> list[Email]:
        return []

    module = module_with(SELECTORS_MODULE, identity_get_current, identity_list_by_email)

    assert signature_violations(module, Role.SELECTORS) == []


def test_the_check_reports_a_positional_argument() -> None:
    def identity_register(email: Email) -> None:
        pass

    module = module_with(SERVICES_MODULE, identity_register)

    assert signature_violations(module, Role.SERVICES) == [
        "tests.sample.services.identity_register: argument 'email' is not keyword-only"
    ]


def test_the_check_reports_an_argument_without_a_type() -> None:
    def identity_register(*, email) -> None:  # type: ignore[no-untyped-def]
        pass

    module = module_with(SERVICES_MODULE, identity_register)

    assert signature_violations(module, Role.SERVICES) == [
        "tests.sample.services.identity_register: argument 'email' has no type"
    ]


def test_the_check_reports_a_raw_str_and_a_raw_dict() -> None:
    def identity_register(*, email: str, extra: dict[str, str]) -> None:
        pass

    module = module_with(SERVICES_MODULE, identity_register)

    assert signature_violations(module, Role.SERVICES) == [
        "tests.sample.services.identity_register: argument 'email' is a raw str",
        "tests.sample.services.identity_register: argument 'extra' is a raw dict",
    ]


def test_the_check_reports_an_http_request_under_another_name() -> None:
    def session_start(*, req: HttpRequest, email: Email) -> None:
        pass

    module = module_with(SERVICES_MODULE, session_start)

    assert signature_violations(module, Role.SERVICES) == [
        "tests.sample.services.session_start: argument 'req' is an HttpRequest "
        "under a name other than 'request'"
    ]


def test_the_check_reports_a_dependency_with_a_default() -> None:
    def identity_register(*, email: Email, hasher: Hasher | None = None) -> None:
        pass

    module = module_with(SERVICES_MODULE, identity_register)

    assert signature_violations(module, Role.SERVICES) == [
        "tests.sample.services.identity_register: dependency 'hasher' has a default"
    ]


def test_the_check_reports_a_service_that_returns_data() -> None:
    def identity_register(*, email: Email) -> Email:
        return email

    module = module_with(SERVICES_MODULE, identity_register)

    assert signature_violations(module, Role.SERVICES) == [
        "tests.sample.services.identity_register: service returns Email instead of None"
    ]


def test_the_check_reports_a_function_without_a_return_type() -> None:
    def identity_get_current(*, email: Email):  # type: ignore[no-untyped-def]
        return email

    module = module_with(SELECTORS_MODULE, identity_get_current)

    assert signature_violations(module, Role.SELECTORS) == [
        "tests.sample.selectors.identity_get_current: function has no return type"
    ]


def test_the_check_reports_a_name_without_entity_and_action() -> None:
    def register(*, email: Email) -> None:
        pass

    def registerIdentity(*, email: Email) -> None:  # noqa: N802
        pass

    module = module_with(SERVICES_MODULE, register, registerIdentity)

    assert signature_violations(module, Role.SERVICES) == [
        "tests.sample.services.register: name does not follow <entity>_<action>",
        "tests.sample.services.registerIdentity: name does not follow <entity>_<action>",
    ]


def test_the_check_skips_private_and_imported_functions() -> None:
    def _hash(password: str) -> str:
        return password

    module = module_with(SERVICES_MODULE, _hash)
    setattr(module, "make_password", make_password)

    assert signature_violations(module, Role.SERVICES) == []


def test_the_check_reports_an_import_of_django_conf() -> None:
    source = (
        "from django.conf import settings\n"
        "import django.conf\n"
        "from django import conf\n"
        "from django.db import transaction\n"
    )

    assert django_conf_imports(source=source, name="tests.sample.services") == [
        "tests.sample.services:1: from django.conf import settings",
        "tests.sample.services:2: import django.conf",
        "tests.sample.services:3: from django import conf",
    ]
