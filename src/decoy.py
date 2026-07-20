from typing import List, Tuple
from src.table.table import Table
from src.table.query import IQuery


class Decoy:
    def __init__(self, number_of_decoys: int):
        self._number_of_decoys = number_of_decoys

    def generate_decoy_table(
        self, table: Table, queries: List[IQuery]
    ) -> Tuple[Table, List[IQuery]]:
        """"""
        new_table = table.copy()
        _, n = new_table.shape

        for _ in range(self._number_of_decoys):
            decoy = [Table.no(True) for i in range(n)]
            new_table.add_row(decoy)

        return new_table, queries
