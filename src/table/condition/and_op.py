from typing import TypeVar

from src.table.condition.base import Comparable
from src.table.condition.composite import CompositeCondition, ICondition


T = TypeVar("T", bound=Comparable)


class AND(CompositeCondition[T]):
    """
    A composite condition that performs logical AND on multiple conditions.
    """
    def __init__(self, *conditions: ICondition[T]):
        super().__init__(*conditions)

    def execute(self, value: T) -> bool:
        """Returns True if all conditions are True."""
        return all(condition.execute(value) for condition in self._conditions)

    def to_string(self) -> str:
        """Returns a string representation of the AND operation."""
        if not self._conditions:
            return "TRUE"
        if len(self._conditions) == 1:
            return self._conditions[0].to_string()
        return "(" + " AND ".join(cond.to_string() for cond in self._conditions) + ")"
