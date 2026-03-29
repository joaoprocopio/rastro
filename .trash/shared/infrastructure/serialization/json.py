import json
from datetime import datetime
from typing import Any


def datetime_encoder(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def to_json(data: Any) -> str:
    return json.dumps(data, default=datetime_encoder)


def from_json(data: str) -> Any:
    return json.loads(data)
