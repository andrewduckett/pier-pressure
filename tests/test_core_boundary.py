"""Task 1.2: the pure core must not import from delivery (design D1)."""

from __future__ import annotations

import ast
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent.parent / "pierpressure" / "core"


def test_pierpressure_imports() -> None:
    import pierpressure

    assert pierpressure.__version__


# Names the pure core must never import: the delivery adapter, the HTTP client,
# and the conditions *provider* package (network lives only at the provider edge,
# design D1/ADR-0005). "pierpressure.conditions" is the provider package and is
# distinct from the core's own "pierpressure.core.conditions" snapshot module.
_FORBIDDEN = ("delivery", "httpx", "pierpressure.conditions")


def _is_forbidden(name: str) -> bool:
    return any(banned in name for banned in _FORBIDDEN)


def test_core_has_no_delivery_or_network_import() -> None:
    for module_path in CORE_DIR.rglob("*.py"):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not _is_forbidden(alias.name), f"{module_path} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert not _is_forbidden(module), f"{module_path} imports from {module}"
