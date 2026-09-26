"""``import apeSees`` must work with only the declared dependencies installed."""

import importlib
import sys

import pytest


def test_import_without_attrs(monkeypatch: pytest.MonkeyPatch) -> None:
    # attrs is not a declared dependency (pyproject.toml), so a clean install
    # may not have it. The attrs distribution provides both the ``attr`` and
    # ``attrs`` packages. A None entry in sys.modules makes an import raise
    # ModuleNotFoundError, as if the package were not installed.
    monkeypatch.setitem(sys.modules, "attr", None)
    monkeypatch.setitem(sys.modules, "attrs", None)

    # Drop cached apeSees modules so the import below runs every module again.
    # monkeypatch puts them back after the test.
    for name in list(sys.modules):
        if name == "apeSees" or name.startswith("apeSees."):
            monkeypatch.delitem(sys.modules, name)

    apesees = importlib.import_module("apeSees")

    assert apesees.RectangularColumnSection is not None
    assert apesees.RectangularSolidSection is not None
