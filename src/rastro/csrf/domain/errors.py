from rastro.common.domain.errors import BaseError


class CsrfFailedError(BaseError):
    code = "csrf.failed"
