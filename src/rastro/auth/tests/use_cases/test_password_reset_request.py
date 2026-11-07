from rastro.auth.application.dtos import PasswordResetRequestInput
from rastro.auth.application.use_cases import password_reset_request
from rastro.auth.domain.value_objects import Email
from rastro.auth.tests.fakes import FakePasswordResetJobs


async def test_it_defers_one_job_with_the_email_address(
    password_reset_jobs: FakePasswordResetJobs,
) -> None:
    await password_reset_request(
        PasswordResetRequestInput(email=Email("ana@x.com")),
        password_reset_jobs=password_reset_jobs,
    )

    assert password_reset_jobs.deferred_sends == [Email("ana@x.com")]
