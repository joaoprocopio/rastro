import random


def always_break() -> None:
    raise Exception("This endpoint always breaks")


def break_50_percent() -> None:
    if random.random() < 0.5:
        raise Exception("This endpoint breaks 50% of the time")


def break_randomly() -> None:
    if random.random() < random.random():
        raise Exception("This endpoint breaks randomly")
