from abc import ABC, abstractmethod
from typing import List, Tuple

from src.table.table import Table
from src.table.query import IQuery


class ClosingStrategy(ABC):
    """Base class for closing strategies."""

    @abstractmethod
    def close(self, table: Table, queries: List[IQuery]) -> Tuple[Table, List[IQuery]]:
        """Closes the table based on the strategy."""
        pass
