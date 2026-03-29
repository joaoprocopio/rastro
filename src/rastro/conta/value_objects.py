from rastro.base.value_objects import ValueObject


class Email(ValueObject[str]):
    def __post_init__(self):
        pass


class Username(ValueObject[str]):
    def __post_init__(self):
        pass


class Name(ValueObject[str]):
    def __post_init__(self):
        pass


class Password(ValueObject[str]):
    def __post_init__(self):
        pass
