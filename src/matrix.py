"""
This module provides a custom Matrix class that extends the sympy.Matrix class.
"""

from typing import List, Sequence, Union
import sympy as sp

from src.table.table import Table
from src.table.query import GroupByQuery, IQuery


class Matrix(sp.Matrix):
    """
    A class that extends sympy.Matrix to provide additional functionality.
    """

    def append_row(self, row: Sequence[Union[int, float]]):
        """
        Appends a row to the matrix.
        """
        return self.col_join(Matrix([row]))

    def append_start_row(self, row: Sequence[Union[int, float]]):
        """
        Appends a row to the start of the matrix.
        """
        return Matrix([row]).col_join(self)

    def append_column(self, column: Sequence[Union[int, float]]):
        """
        Appends a column to the matrix.
        """
        return self.row_join(Matrix([column]).T)

    def show(self) -> str:
        """
        Returns a string representation of the matrix.
        """
        return sp.pretty(self)

    def __str__(self) -> str:
        return self.show()

    @staticmethod
    def from_group_by_queries(table: Table, queries: List[GroupByQuery]) -> "Matrix":
        """
        Creates a Matrix from a list of group by queries.
        """

        vectorized_queries: List[List[int]] = []
        for query in queries:
            vectors = query.as_vector(table)
            for v in vectors.values():
                vectorized_queries.append(v)

        return Matrix(vectorized_queries)

    @staticmethod
    def from_queries(table: Table, queries: List[IQuery]) -> "Matrix":
        """
        Creates a Matrix from a list of select where queries.
        """
        return Matrix([q.as_vector(table) for q in queries])
