from rastro.common.domain.errors import BaseError


class CsrfFailedError(BaseError):
    code = "security.csrf_failed"
