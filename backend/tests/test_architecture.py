import ast
from pathlib import Path


def test_inner_layers_do_not_depend_on_frameworks_or_adapters():
    root = Path(__file__).parents[1] / "app"
    for layer, allowed in [
        ("domain", ("app.domain",)),
        ("application", ("app.domain", "app.application")),
    ]:
        for path in (root / layer).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                imports = []
                if isinstance(node, ast.ImportFrom):
                    imports = [node.module or ""]
                elif isinstance(node, ast.Import):
                    imports = [item.name for item in node.names]
                for module in imports:
                    assert not module.startswith(
                        ("fastapi", "sqlalchemy", "pydantic")
                    ), (path, module)
                    assert not module.startswith("app.") or module.startswith(
                        allowed
                    ), (path, module)


def test_http_routes_do_not_query_the_database():
    routes = Path(__file__).parents[1] / "app/api/v1/routes"
    for path in routes.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(
                    ("sqlalchemy", "app.infrastructure")
                ), path
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"query", "commit", "flush", "refresh"}, (
                    path
                )
