"""Shared pytest setup for apeSees.

1. Put this checkout's ``src/`` first on ``sys.path``, so the tests exercise
   the working tree and not an editable install that points at another clone.
2. Use a non-interactive matplotlib backend; every apeSees module imports
   ``matplotlib.pyplot``.
3. openseespy is not importable on every interpreter (on Windows it can raise
   ``RuntimeError: Failed to import openseespy``). apeSees imports it at module
   level everywhere, but the pure-numpy parts, such as the loading protocols,
   only call it in ``build()``. When the real module can't be imported, an
   empty stand-in is registered so those parts can still be tested. Any call
   into OpenSees then fails with ``AttributeError`` instead of passing quietly.
"""

import os
import sys
import types
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

os.environ.setdefault("MPLBACKEND", "Agg")

try:
    import openseespy.opensees  # noqa: F401
except Exception:  # ImportError, or RuntimeError from openseespy on Windows
    _pkg = types.ModuleType("openseespy")
    _pkg.opensees = types.ModuleType("openseespy.opensees")  # type: ignore[attr-defined]
    sys.modules["openseespy"] = _pkg
    sys.modules["openseespy.opensees"] = _pkg.opensees  # type: ignore[attr-defined]
