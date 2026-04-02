from pydantic import RootModel


class Id(RootModel[int]):
    pass


print(Id(1))
print(Id.model_validate_json("nul"))
