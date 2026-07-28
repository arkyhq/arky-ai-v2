"""Read-only source compilation checks."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_python_sources_compile() -> None:
    """Compile every repository Python source without writing bytecode."""
    for path in PROJECT_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
