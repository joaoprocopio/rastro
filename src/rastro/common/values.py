from dataclasses import dataclass
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class InvalidValueError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class StrValueObject:
    value: str

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        from_str = core_schema.no_info_after_validator_function(
            cls, core_schema.str_schema()
        )
        return core_schema.json_or_python_schema(
            json_schema=from_str,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(cls), from_str]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda value_object: value_object.value
            ),
        )
