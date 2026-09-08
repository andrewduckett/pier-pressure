"""Task 1.2: the pure core must not import from delivery (design D1)."""

from __future__ import annotations

import ast
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent.parent / "pierpressure" / "core"


def test_pierpressure_imports() -> None:
    import pierpressure

    assert pierpressure.__version__


def test_core_has_no_delivery_import() -> None:
    for module_path in CORE_DIR.rglob("*.py"):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "delivery" not in alias.name, f"{module_path} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert "delivery" not in module, f"{module_path} imports from {module}"
