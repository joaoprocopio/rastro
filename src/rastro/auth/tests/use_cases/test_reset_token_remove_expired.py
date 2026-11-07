from rastro.auth.application.dtos import ResetTokenRemoveExpiredOutput
from rastro.auth.application.use_cases import reset_token_remove_expired
from rastro.auth.domain.aggregates import IssuedResetToken, User
from rastro.auth.domain.value_objects import ResetToken
from rastro.auth.tests.fakes import FakeClock, FakeResetTokenRepository


async def test_it_removes_the_reset_tokens_that_expired_at_the_time_of_the_clock(
    reset_tokens: FakeResetTokenRepository,
    clock: FakeClock,
    ana: User,
    reset_token: ResetToken,
    expired_reset_token: IssuedResetToken,
) -> None:
    output = await reset_token_remove_expired(reset_tokens=reset_tokens, clock=clock)

    assert output == ResetTokenRemoveExpiredOutput(count=1)
    assert list(reset_tokens.reset_tokens) == [ana.id]
