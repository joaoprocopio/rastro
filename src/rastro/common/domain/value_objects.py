from typing import Annotated

from pydantic import Field, PositiveInt, StringConstraints

from rastro.common.domain.schemas import RootSchema, Schema

_LABEL = r"[a-z0-9]([a-z0-9-]*[a-z0-9])?"
_HOST = rf"({_LABEL}(\.{_LABEL})*|\[[0-9a-f]*(:[0-9a-f]*){{2,7}}\])"
_PORT_FROM_10000 = (
    r"[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]"
)
# A browser omits the default port of the scheme, so an origin never holds it.
_HTTP_PORT = rf"[1-9]|[1-79][0-9]|8[1-9]|[1-9][0-9]{{2,3}}|{_PORT_FROM_10000}"
_HTTPS_PORT = (
    rf"[1-9][0-9]?|[1-35-9][0-9]{{2}}|4[0-35-9][0-9]|44[0-24-9]|[1-9][0-9]{{3}}"
    rf"|{_PORT_FROM_10000}"
)
# A browser sends an origin as a scheme, a host, and an optional port, with no path.
CORS_ORIGIN_PATTERN = (
    rf"^(http://{_HOST}(:({_HTTP_PORT}))?|https://{_HOST}(:({_HTTPS_PORT}))?)$"
)


class ValueObject(Schema):
    pass


class RootValueObject[T](RootSchema[T]):
    pass


class Id(RootValueObject[PositiveInt]):
    pass


# A token shorter than 16 random bytes is short enough to guess.
class TokenBytes(RootValueObject[Annotated[int, Field(ge=16, strict=False)]]):
    pass


class CorsOrigin(
    RootValueObject[Annotated[str, StringConstraints(pattern=CORS_ORIGIN_PATTERN)]]
):
    pass
