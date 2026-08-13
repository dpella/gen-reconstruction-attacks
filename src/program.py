from datetime import datetime
from typing import List, Optional

from src.common import Range
from src.logger import Logger, Level
from src.table.table import Table
from src.table.condition import EQ
from src.table.query import IQuery, SelectQuery, SelectWhereQuery
from src.search.search import Search
from src.compress import Compress
from src.matrix import Matrix
from src.hadamard import Hadamard
from src.decoy import Decoy


class Program:
    def __init__(self, log_level: str, log_file: Optional[str] = None):
        self.__logger = Logger.get_instance()
        level = Level[log_level.upper()]
        self.__logger.set_level(level.value)
        if log_file:
            self.__logger.set_log_file(log_file)

        self.__number_of_records: Optional[int] = None
        self.__population_value: float = 0.0
        self.__communality_value: float = 0.0
        self.__titles: List[str] = []
        self.__new_titles: List[str] = []
        self.__sensitive_column: Optional[str] = None
        self.__seed_value: Optional[int] = None
        self.__columns_to_compress: List[List[str]] = []
        self.__start_date: Optional[str] = None

    def set_number_of_records(self, n: int) -> "Program":
        self.__number_of_records = n
        return self

    def set_population_value(self, population_value: float) -> "Program":
        self.__population_value = population_value
        return self

    def set_communality_value(self, communality_value: float) -> "Program":
        self.__communality_value = communality_value
        return self

    def set_titles(self, titles: List[str]) -> "Program":
        self.__titles = titles
        return self

    def set_new_titles(self, new_titles: List[str]) -> "Program":
        self.__new_titles = new_titles
        return self

    def set_sensitive_column(self, sensitive_column: str) -> "Program":
        self.__sensitive_column = sensitive_column
        return self

    def set_seed_value(self, seed_value: int) -> "Program":
        self.__seed_value = seed_value
        return self

    def set_columns_to_compress(self, columns: List[List[str]]) -> "Program":
        self.__columns_to_compress = columns
        return self

    def set_start_date(self, start_date: str) -> "Program":
        self.__start_date = start_date
        return self

    def set_compressed_title(self, compressed_title: str) -> "Program":
        self.__compressed_title = compressed_title
        return self

    def set_interval_length(self, interval_length: List[int]) -> "Program":
        self.__interval_length = interval_length
        return self

    def set_hadamard_order(self, order: int) -> "Program":
        self.__hadamard_order = order
        return self

    def set_number_of_decoys(self, number_of_decoys: int) -> "Program":
        self.__number_of_decoys = number_of_decoys
        return self

    def __exclude_decoys_from_catchall_query(
        self, queries: List[IQuery], binary_column_name: Optional[str]
    ) -> List[IQuery]:
        """
        The Hadamard expansion appends one unconditional `SELECT AVG(...)
        FROM table;` query with no WHERE clause, so it has no predicate to
        exclude decoy rows from — every decoy would be silently counted by
        it. Replace it with the negation (`= '0'`) of the `= '1'` query on
        the one column whose real values are exactly '0'/'1' (see
        `Hadamard.binary_column_name`); together the `= '1'` and `= '0'`
        queries partition the reconstructable rows exactly like the
        original catch-all query did, but both have a WHERE clause a decoy
        row can't satisfy.

        No-op if there is no catch-all query to replace (e.g. no Hadamard
        expansion was used).
        """
        catchall_indices = [
            i
            for i, q in enumerate(queries)
            if isinstance(q, SelectQuery) and not isinstance(q, SelectWhereQuery)
        ]
        if not catchall_indices:
            return queries

        if len(catchall_indices) != 1 or binary_column_name is None:
            raise ValueError(
                "Cannot safely add decoys: expected exactly one catch-all "
                "all-records query together with a known binary column to "
                "negate it with, but found "
                f"{len(catchall_indices)} catch-all queries and "
                f"binary_column_name={binary_column_name!r}."
            )

        index = catchall_indices[0]
        negation = SelectWhereQuery(
            self.__sensitive_column or Table.SENSITIVE_COL_NAME,
            binary_column_name,
            EQ(binary_column_name, Table.no(False)),
        )
        return queries[:index] + [negation] + queries[index + 1 :]

    def run(self) -> None:
        if self.__number_of_records is None:
            raise ValueError("The number of records must be set.")

        self.__logger.info(
            f"Creating a table with number-of-records: {self.__number_of_records}"
        )
        table = Table.create_table_with_n_records(
            self.__number_of_records,
            self.__population_value,
            self.__titles,
            self.__seed_value,
        )
        if self.__sensitive_column:
            table.set_sensitive_column_name(self.__sensitive_column)
        self.__logger.creation(f"The initial table of {table.shape}:\n{table.show()}")

        search = Search(
            self.__population_value, self.__communality_value, self.__new_titles
        )
        new_table, queries = search.generate_fullrank_table(table)

        binary_column_name: Optional[str] = None
        if self.__hadamard_order:
            hadamard = Hadamard(self.__logger, self.__seed_value)
            matrix = Matrix.from_queries(new_table, queries[:-1])
            new_table, queries = hadamard.generate_new_table(
                matrix, self.__hadamard_order, self.__new_titles
            )
            binary_column_name = hadamard.binary_column_name

        if self.__number_of_decoys and self.__number_of_decoys > 0:
            queries = self.__exclude_decoys_from_catchall_query(
                queries, binary_column_name
            )
            decoy = Decoy(self.__number_of_decoys)
            new_table, queries = decoy.generate_decoy_table(new_table, queries)

        if self.__columns_to_compress:
            for i, columns in enumerate(self.__columns_to_compress):
                interval = 1

                if self.__interval_length and i < len(self.__interval_length):
                    interval = self.__interval_length[i]

                compress = (
                    Compress(new_table)
                    .set_columns_to_compress(columns)
                    .set_column_title(f"{self.__compressed_title}_{i}")
                    .set_interval_length(interval)
                )

                if self.__start_date:
                    compress = compress.set_start_date(
                        datetime.strptime(self.__start_date, "%Y-%m-%d").date()
                    )

                new_table, queries = compress.compress(queries)

        self.__logger.info(f"The new table:\n{new_table.show()}")
        self.__logger.info("Generated queries:\n" + "\n".join(q.sql for q in queries))

        # Run the attack
        if self.__logger.level <= Level.ATTACK.value:
            self.__logger.attack(
                f"Running the attack on the table with {len(queries)} queries."
            )

            aggregated_queries: List[float] = []
            for query in queries:
                result = query(new_table)
                vector = query.as_vector(new_table)
                aggregated_queries.append(result * sum(vector))

            self.__logger.attack(
                f"The aggregated queries results: {aggregated_queries}"
            )
            matrix = Matrix.from_queries(new_table, queries)
            matrix = matrix.append_column(aggregated_queries)
            self.__logger.attack(
                f"The augmented matrix of the linear equations system:\n{matrix.show()}"
            )
            solution = Matrix(matrix.rref()[0])
            self.__logger.attack(
                f"The solution of the linear equations system:\n{solution.show()}"
            )
