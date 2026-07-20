"""
This module provides the Search class for generating a full rank matrix
and k-anonymous table from an initial table and its initial queries.
"""

from typing import List, Tuple
from cvxpy import Problem, Minimize, Constraint, Variable, GLPK_MI, sum
from cvxpy.constraints.zero import Zero
from numpy import array

from src.logger import Logger
from src.table.table import Table
from src.table.query import SelectWhereQuery, IQuery
from src.table.condition import EQ
from src.matrix import Matrix
from src.search.closing import (
    ClosingStrategy,
    AllClosingStrategy,
    LastNegationClosingStrategy,
    NoopClosingStrategy,
)


class Search:
    def __init__(
        self, population_value: float, communality_value: float, titles: List[str] = []
    ):
        self._population_value = population_value
        self._communality_value = communality_value
        self._titles = titles
        self._logger = Logger.get_instance()

    def _get_new_title(self, table: Table, k: int) -> str:
        """
        Gets a new title for a column.
        """
        if k < len(self._titles):
            return self._titles[k]

        return table.generate_new_title()

    def generate_constraints(
        self, matrix: Matrix, v: Variable,
    ) -> List[Constraint]:
        """
        Generates constraints for the optimization problem.
        """
        m, n = matrix.shape

        return [
            Zero(sum(v) - round(n * self._population_value)),  # ||v||^2 == n * p
            Zero(
                array(matrix.tolist()) @ v
                - array([round(n * self._communality_value) for _ in range(m)])
            ),  # ||Mv|| == n * c
        ]

    def generate_li_vector(self, matrix: Matrix) -> List[int]:
        """
        Create a new vector that is LI of all row vectors.
        """
        self._logger.debug(f"Generating LI vector for matrix with shape {matrix.shape}")

        _, n = matrix.shape
        v = Variable(n, boolean=True)

        constraints = self.generate_constraints(matrix, v)
        objective = Minimize(0)

        problem = Problem(objective, constraints)
        problem.solve(solver=GLPK_MI)

        if v.value is not None:
            self._logger.debug(
                f"Generated vector: {v.value} with status: {problem.status}"
            )
            return [int(x) for x in v.value]

        raise Exception("no optimal solution")

    def _generate_initial_queries(self, initial: Table) -> List[IQuery]:
        """
        Generates initial queries for the table.
        """
        queries: List[IQuery] = [
            SelectWhereQuery(
                initial.sensitive_column_name, title, EQ(title, Table.yes())
            )
            for title in initial.titles
        ]
        self._logger.debug(f"Initial queries: {[query.sql for query in queries]}")

        return queries

    def generate_fullrank_matrix(self, initial: Matrix) -> Matrix:
        """
        Generates a full rank matrix.
        """
        _, n = initial.shape
        matrix = initial.copy()
        stop_condition = (
            n - 1
            if self._population_value == 0.5 and self._communality_value == 0.25
            else n
        )

        while matrix.rank() < stop_condition:
            try:
                v = self.generate_li_vector(matrix)

            except Exception as e:
                self._logger.debug(f"Error generating LI vector: {e}")
                self._logger.debug(
                    f"The last matrix of rank: {matrix.rank()} is not full rank:\n{matrix.show()}"
                )
                break

            self._logger.debug(f"Generated new vector: {v}")

            matrix = matrix.append_row(v)

            self._logger.debug(
                f"Updated matrix with rank {matrix.rank()}:\n{matrix.show()}"
            )

        if matrix.rank() != matrix.shape[1]:
            self._logger.warning(
                f"The matrix rank ({matrix.rank()}) is not equal to the number of columns ({matrix.shape[1]})."
            )
            if matrix.rank() != n - 1:
                raise Exception(
                    f"No optimal solution found. The matrix of rank ({matrix.rank()}) is not full rank."
                )

        self._logger.creation(
            f"Final matrix with rank {matrix.rank()}:\n{matrix.show()}"
        )

        return matrix

    def _set_closing_strategy(self, matrix: Matrix) -> ClosingStrategy:
        """
        Sets the closing strategy for the search.
        """
        if matrix.rank() == matrix.shape[1]:
            self._logger.debug("Matrix is already full rank. No closing needed.")
            return NoopClosingStrategy()
        elif self._population_value == 0.5 and self._communality_value == 0.25:
            self._logger.debug(
                "Using LastNegationClosingStrategy for closing the table."
            )
            return LastNegationClosingStrategy()

        self._logger.debug("Using AllClosingStrategy for closing the table.")
        return AllClosingStrategy()

    def generate_fullrank_table(self, initial: Table) -> Tuple[Table, List[IQuery]]:
        """
        Generates a full rank table.
        """
        queries = self._generate_initial_queries(initial)

        matrix = self.generate_fullrank_matrix(Matrix.from_queries(initial, queries))
        m, n = matrix.shape
        number_titles = len(initial.titles)
        new_table = initial.copy()

        for k in range(1, m):
            new_title = self._get_new_title(new_table, k + 1 - number_titles)
            query = SelectWhereQuery(
                new_table.sensitive_column_name, new_title, EQ(new_title, Table.yes())
            )
            row = matrix.row(k)

            new_table.add_column(
                new_title,
                [Table.yes() if i else Table.no(k + 1 != n - 1) for i in row],
            )
            queries += [query]

            self._logger.debug(f"Added new column to the table:\n{new_table.show()}")

        closing_strategy: ClosingStrategy = self._set_closing_strategy(matrix)
        return closing_strategy.close(new_table, queries)
