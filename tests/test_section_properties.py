"""SectionProperties keeps the methods attr.dataclass generated for it."""

import pytest

from apeSees.section import rectangularColumn, rectangularSolidSection


@pytest.mark.parametrize(
    "cls",
    [rectangularColumn.SectionProperties, rectangularSolidSection.SectionProperties],
    ids=["RectangularColumn", "RectangularSolid"],
)
def test_section_properties_eq_order_repr(cls) -> None:
    n = len(cls.__match_args__)
    small = cls(*([1.0] * n))
    big = cls(*([1.0] * (n - 1) + [2.0]))

    assert small == cls(*([1.0] * n)) and small != big
    # attr.dataclass (classic attr.s) generated ordering; it is kept.
    assert small < big and small <= big and big > small and big >= small
    assert cls.__hash__ is None
    assert repr(small).startswith("SectionProperties(A_g=1.0, ")
