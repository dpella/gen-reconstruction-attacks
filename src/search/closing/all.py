from typing import List, Tuple

from src.search.closing.base import ClosingStrategy
from src.table.condition.eq import EQ
from src.table.table import Table
from src.table.query import IQuery, SelectQuery


class AllClosingStrategy(ClosingStrategy):
    """Closes the table by adding the query that selects all rows."""

    def close(self, table: Table, queries: List[IQuery]) -> Tuple[Table, List[IQuery]]:
        all_query = SelectQuery(table.sensitive_column_name)

        return table, queries + [all_query]
