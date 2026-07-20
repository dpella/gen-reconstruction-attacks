from typing import List, Tuple

from src.search.closing.base import ClosingStrategy
from src.table.condition.eq import EQ
from src.table.table import Table
from src.table.query import IQuery, SelectWhereQuery


class LastNegationClosingStrategy(ClosingStrategy):
    def close(self, table: Table, queries: List[IQuery]) -> Tuple[Table, List[IQuery]]:
        last_title = table.titles[-1]
        last_query = SelectWhereQuery(
            table.sensitive_column_name,
            last_title,
            EQ(last_title, Table.no(False)),
        )

        return table, queries + [last_query]
