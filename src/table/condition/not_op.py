from typing import TypeVar

from src.table.condition.base import ICondition, Comparable


T = TypeVar("T", bound=Comparable)


class NOT(ICondition[T]):
    """
    A condition that negates another condition.
    """
    def __init__(self, condition: ICondition[T]):
        self._condition = condition

    def execute(self, value: T) -> bool:
        """Returns the negation of the wrapped condition."""
        return not self._condition.execute(value)

    def to_string(self) -> str:
        """Returns a string representation of the NOT operation."""
        return f"(NOT {self._condition.to_string()})"
