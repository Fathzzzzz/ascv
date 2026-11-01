"""Architecture guard: core must stay runnable without the API layer.

Parsing the AST (instead of importing) keeps the check independent of whatever
is installed, so it also fails fast on a bare checkout.
"""

import ast
from pathlib import Path

import pytest

CORE_DIR = Path(__file__).resolve().parents[1] / "core"
FORBIDDEN_ROOTS = {"fastapi", "starlette", "app"}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def core_modules() -> list[Path]:
    return sorted(CORE_DIR.rglob("*.py"))


def test_core_has_modules_to_check() -> None:
    assert core_modules(), "core package is missing"


@pytest.mark.parametrize("module", core_modules(), ids=lambda path: path.name)
def test_core_never_imports_the_api_layer(module: Path) -> None:
    violations = imported_roots(module) & FORBIDDEN_ROOTS
    assert not violations, f"{module.name} imports {sorted(violations)}"


def test_no_module_imports_rembg_at_module_level() -> None:
    """Heavy models load lazily, so tests and imports stay fast and offline."""
    for module in core_modules():
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        top_level_imports: set[str] = set()
        for node in tree.body:  # module scope only, not inside functions
            if isinstance(node, ast.Import):
                top_level_imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                top_level_imports.add(node.module.split(".")[0])
        assert "rembg" not in top_level_imports, f"{module.name} imports rembg eagerly"
