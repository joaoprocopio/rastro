import ast

from tests.architecture.rules import rastro_sources


def test_no_class_is_named_base_model() -> None:
    classes = [
        f"{name}:{node.lineno}"
        for name, source in rastro_sources()
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ClassDef) and node.name == "BaseModel"
    ]

    assert classes == []
