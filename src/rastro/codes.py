import enum


@enum.unique
class ErrorCode(enum.StrEnum):
    """The application's catalog of error codes."""

    BASE_VALIDATION_ERROR = "BASE_VALIDATION_ERROR"
    AUTH_CREDENCIAIS_INCORRETAS = "AUTH_CREDENCIAIS_INCORRETAS"
    AUTH_CONTA_NAO_ENCONTRADA = "AUTH_CONTA_NAO_ENCONTRADA"
