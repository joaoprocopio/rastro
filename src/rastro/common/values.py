from pydantic import ConfigDict, RootModel


class ValueObject[T](RootModel[T]):
    model_config = ConfigDict(frozen=True)
