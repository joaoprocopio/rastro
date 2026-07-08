from http import HTTPStatus

from rastro.codes import ErrorCode
from rastro_base.error import BaseError


class CredenciaisIncorretasError(BaseError):
    code = ErrorCode.AUTH_CREDENCIAIS_INCORRETAS
    status = HTTPStatus.UNAUTHORIZED
    title = "Credenciais incorretas"


class ContaNaoEncontradaError(BaseError):
    code = ErrorCode.AUTH_CONTA_NAO_ENCONTRADA
    status = HTTPStatus.NOT_FOUND
    title = "Conta não encontrada"
