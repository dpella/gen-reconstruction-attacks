from typing import TypeVar

from src.table.condition.base import ICondition, Comparable


T = TypeVar("T", bound=Comparable)


class LEQT(ICondition[T]):
    """
    A condition that checks for less-than-or-equal-to comparison between two values.
    """
    def __init__(self, column: str, target: T):
        self._column = column
        self._target = target

    def execute(self, value: T) -> bool:
        return value <= self._target

    def to_string(self) -> str:
        if isinstance(self._target, str):
            return f"{self._column} <= '{self._target}'"
        return f"{self._column} <= {self._target}"
