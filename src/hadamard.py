from typing import List, Optional, Tuple
from src.logger import Logger
from src.matrix import Matrix
from src.table.table import Table
from src.table.query import (
    IQuery,
    SelectWhereQuery,
    SelectQuery,
)
from src.table.condition import EQ


class Hadamard:
    def __init__(self, logger: Logger, seed: Optional[int] = None):
        self.__logger = logger
        self._sensitive_column_name = Table.SENSITIVE_COL_NAME
        self.__seed = seed
        self.binary_column_name: Optional[str] = None

    def set_sensitive_column_name(self, name: str) -> "Hadamard":
        self._sensitive_column_name = name
        return self

    def generate_new_matrix(self, H: Matrix, k: int) -> Matrix:
        """
        Generate a new matrix of size k times the size of the original matrix
        """
        if k == 1:
            return H

        H_op = H.applyfunc(lambda x: (x + 1) % 2)
        top = Matrix.vstack(H, H)
        bottom = Matrix.vstack(H, H_op)

        return self.generate_new_matrix(Matrix.hstack(top, bottom), k - 1)

    def generate_new_table(
        self, H: Matrix, k: int, titles: List[str]
    ) -> Tuple[Table, List[IQuery]]:
        """
        Generate a new table from the Hadamard matrix of order k.
        """
        new_matrix = H.append_start_row([1] * H.cols)  # Add the last row of all 1s
        new_matrix = self.generate_new_matrix(new_matrix, k)
        self.__logger.creation(
            f"The Hadamard matrix of order {k}:\n{new_matrix.show()}"
        )
        queries: List[IQuery] = []
        table = Table(titles, [], self.__seed)
        table.set_sensitive_column_name(self._sensitive_column_name)

        _, n = new_matrix.shape
        for i in range(1, n):
            row = new_matrix.row(i)

            new_title = table.generate_new_title()
            query = SelectWhereQuery(
                table.sensitive_column_name, new_title, EQ(new_title, Table.yes())
            )

            # At this one iteration, "no" answers are the literal '0' rather
            # than a randomized '2'/'3' — every value in this column is
            # exactly '0' or '1'. That makes it the only column whose
            # `= '0'` query is the true negation of its `= '1'` query,
            # needed to safely rewrite the catch-all all-records query below
            # when decoys are added (see Program.run / Decoy).
            is_deterministic = i + 1 == n - 1
            if is_deterministic:
                self.binary_column_name = new_title

            table.add_column(
                new_title,
                [Table.yes() if j else Table.no(not is_deterministic) for j in row],
            )
            queries += [query]

        queries += [
            SelectQuery(table.sensitive_column_name),
        ]
        table.initialize_sensitive_column()

        return table, queries
