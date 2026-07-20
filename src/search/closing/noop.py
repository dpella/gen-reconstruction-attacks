from typing import List, Tuple

from src.search.closing.base import ClosingStrategy
from src.table.query import IQuery
from src.table.table import Table


class NoopClosingStrategy(ClosingStrategy):
    def close(self, table: Table, queries: List[IQuery]) -> Tuple[Table, List[IQuery]]:
        return table, queries
