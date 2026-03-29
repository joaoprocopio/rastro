def parse_csv(value: str | list[str]) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",")]

    return value


def parse_booleanish(raw_value: str | bool) -> bool:
    if type(raw_value) is bool:
        return raw_value

    value = raw_value.lower()

    if value == "true" or value == "1":
        return True

    if value == "false" or value == "0":
        return False

    raise TypeError(f"Could not parse {raw_value} as booleanish value.")
