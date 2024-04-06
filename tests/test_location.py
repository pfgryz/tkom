import pytest

from src.location import Location
from src.position import Position


def test_location():
    location = Location(
        Position(1, 1),
        Position(1, 5)
    )

    assert location.begin.line == 1
    assert location.begin.column == 1
    assert location.end.column == 5


def test_location_invalid_type():
    with pytest.raises(TypeError):
        Location(3, Position(1, 5))


def test_location_invalid_begin_position_greater_line():
    with pytest.raises(ValueError):
        Location(
            Position(3, 1),
            Position(2, 4)
        )


def test_location_invalid_begin_position():
    with pytest.raises(ValueError):
        Location(
            Position(3, 10),
            Position(3, 4)
        )