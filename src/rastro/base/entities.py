from rastro.base.value_objects import ValueObject


class Id(ValueObject[str]):
    def __post_init__(self) -> None:
        pass


# abc = Id()
# abc.cop
print(Id(1) == 
      Id(2))
