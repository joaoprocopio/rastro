from rastro.base.value_objects import ValueObject


class Id(ValueObject[int]):
    def validate(self) -> None:
        if not self.value >= 1:
            raise ValueError()


id1 = Id(1)
id2 = Id(2)
id1_2 = Id(1)

idBREAKS = Id(-1)

print(id1)
print(id2)
print(id1 == id2)
print(id1 == id1_2)
