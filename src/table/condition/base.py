from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Protocol

T = TypeVar("T", contravariant=True)


class Comparable(Generic[T], Protocol):
    """A base class for comparable types."""

    @abstractmethod
    def __lt__(self, other: T) -> bool:
        pass

    @abstractmethod
    def __gt__(self, other: T) -> bool:
        pass

    @abstractmethod
    def __le__(self, other: T) -> bool:
        pass

    @abstractmethod
    def __ge__(self, other: T) -> bool:
        pass


K = TypeVar("K", bound=Comparable)


class ICondition(Generic[K], ABC):
    @abstractmethod
    def execute(self, value: K) -> bool:
        """
        Execute the condition on the given value.
        """
        pass

    @abstractmethod
    def to_string(self) -> str:
        """
        Return a string representation of the condition.
        """
        pass
