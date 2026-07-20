from abc import abstractmethod
from typing import List, TypeVar

from src.table.condition.base import ICondition, Comparable


T = TypeVar("T", bound=Comparable)


class CompositeCondition(ICondition[T]):
    """
    Base class for composite conditions that combine multiple conditions.
    Implements the Composite pattern.
    """
    def __init__(self, *conditions: ICondition[T]):
        self._conditions: List[ICondition[T]] = list(conditions)

    def add(self, condition: ICondition[T]) -> "CompositeCondition[T]":
        """Add a condition to the composite."""
        self._conditions.append(condition)
        return self

    def remove(self, condition: ICondition[T]) -> "CompositeCondition[T]":
        """Remove a condition from the composite."""
        self._conditions.remove(condition)
        return self

    @property
    def conditions(self) -> List[ICondition[T]]:
        """Get all conditions in the composite."""
        return self._conditions

    @abstractmethod
    def execute(self, value: T) -> bool:
        """Execute the composite condition."""
        pass

    @abstractmethod
    def to_string(self) -> str:
        """Return string representation of the composite condition."""
        pass
