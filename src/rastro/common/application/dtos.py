import re
from typing import Any, Self

import pydantic

from rastro.common.domain.schemas import Schema

# RFC 9457 section 3.2: a letter, then letters, digits, or "_", three characters at least.
_EXTENSION_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")


class DTO(Schema):
    pass


class ExtensibleDTO(DTO):
    extensions: Schema | None = pydantic.Field(default=None, exclude=True)

    @pydantic.model_validator(mode="after")
    def _check_extension_names(self) -> Self:
        if self.extensions is None:
            return self
        members = type(self).model_fields.keys() - {"extensions"}
        for name in type(self.extensions).model_fields:
            if name in members:
                raise ValueError(
                    f"The extension {name!r} is a member of {type(self).__name__}."
                )
            if _EXTENSION_NAME.fullmatch(name) is None:
                raise ValueError(
                    f"The extension {name!r} breaks the RFC 9457 naming rule."
                )
        return self

    @pydantic.model_serializer(mode="wrap")
    def _serialize_extensions_at_the_top_level(
        self, handler: pydantic.SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        members: dict[str, Any] = {
            name: value for name, value in handler(self).items() if value is not None
        }
        if self.extensions is not None:
            members |= self.extensions.model_dump(mode="json", exclude_none=True)
        return members
