from typing import Iterable, Union
from datetime import date

DEFAULT_DATE = date(2019, 1, 1)
"""
A default date used for compressing binary columns into date ranges.
This date serves as a starting point for the compression process.
"""


class Range:
    """Represents a range of int as a tuple (start, end)."""

    def __init__(self, start: int, end: int):
        self._range = (start, end)

    def __iter__(self):
        return iter(self._range)

    def __getitem__(self, index: int) -> int:
        if index < 0 or index >= 2:
            raise IndexError("Index must be 0 or 1.")
        return self._range[index]

    def __repr__(self) -> str:
        start, end = self._range
        return f"Range({start}, {end})"


def avg(values: Iterable[Union[int, float]]) -> float:
    """
    Calculates the average of a list of numeric values.
    Returns 0 if the input is empty.
    """
    if not values:
        return 0.0

    sum_values = 0
    count = 0

    for value in values:
        sum_values += value
        count += 1

    return sum_values / count
