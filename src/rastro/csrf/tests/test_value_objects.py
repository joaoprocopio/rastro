from rastro.common.domain.value_objects import TokenBytes
from rastro.csrf.domain.value_objects import CsrfToken


def test_a_csrf_token_of_16_bytes_has_22_characters() -> None:
    token = CsrfToken.generate(nbytes=TokenBytes(16))

    assert len(token.root.get_secret_value()) == 22


def test_a_csrf_token_hides_its_value_in_repr() -> None:
    token = CsrfToken.model_validate("abc123")

    assert "**********" in repr(token)
    assert "abc123" not in repr(token)


def test_a_csrf_token_matches_a_token_with_the_same_value() -> None:
    assert CsrfToken.model_validate("abc123").matches(
        CsrfToken.model_validate("abc123")
    )


def test_a_csrf_token_does_not_match_a_token_with_another_value() -> None:
    assert not CsrfToken.model_validate("abc123").matches(
        CsrfToken.model_validate("abc124")
    )


def test_a_csrf_token_does_not_match_a_value_with_a_character_outside_ascii() -> None:
    assert not CsrfToken.model_validate("token").matches(
        CsrfToken.model_validate("tökén")
    )
