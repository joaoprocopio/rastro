from tests.architecture.rules import rastro_sources, validation_violations


def test_no_rastro_code_calls_full_clean_or_defines_clean() -> None:
    violations = [
        violation
        for name, source in rastro_sources()
        for violation in validation_violations(source=source, name=name)
    ]

    assert violations == []


def test_the_check_reports_each_forbidden_validation_call() -> None:
    source = (
        "def identity_register(*, identity):\n"
        "    identity.full_clean()\n"
        "    identity.clean_fields(exclude=['password'])\n"
        "    identity.validate_unique()\n"
        "    identity.validate_constraints()\n"
        "    identity.save()\n"
    )

    assert validation_violations(source=source, name="tests.sample.services") == [
        "tests.sample.services:2: calls full_clean()",
        "tests.sample.services:3: calls clean_fields()",
        "tests.sample.services:4: calls validate_unique()",
        "tests.sample.services:5: calls validate_constraints()",
    ]


def test_the_check_reports_a_model_that_defines_clean() -> None:
    source = (
        "from django.db import models\n"
        "\n"
        "\n"
        "class Identity(models.Model):\n"
        "    def clean(self) -> None:\n"
        "        pass\n"
        "\n"
        "    def save(self, *args, **kwargs):\n"
        "        pass\n"
    )

    assert validation_violations(source=source, name="tests.sample.models") == [
        "tests.sample.models:5: Identity defines clean()",
    ]
