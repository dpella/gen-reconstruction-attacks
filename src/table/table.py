"""
This module defines a Table class that represents a table of data
and a Query class that represents a SQL query.
"""

from datetime import date
from typing import Dict, List, Optional, Union, cast
from itertools import product
from random import shuffle, randint, seed, sample
from tabulate import tabulate


class Table:
    """
    A class that represents a table of data.
    """

    DEFAULT_COLS = 1
    SENSITIVE_COL_NAME = "s"

    def __init__(
        self, titles: List[str], data: List[List[str]], seed_value: Optional[int] = None
    ):
        """
        Initializes the Table with the given data.
        """
        self._titles = titles
        self._initial_titles = titles.copy()
        self.table: Dict[str, Union[List[str], List[date], List[int], List[float]]] = {
            title: cast(List[str], []) for title in self.titles
        }
        if seed_value is not None:
            self._seed = seed_value
            seed(seed_value)

        self.initialize_table(data)
        if data:
            self.initialize_sensitive_column()

        self._sensitive_column_name = self.SENSITIVE_COL_NAME

    def initialize_table(self, data: List[List[str]]):
        """
        Initializes the table with the given data.
        """
        if len(data) == 0:
            return

        # Check if the number of columns in each row matches the number of titles.
        for row in data:
            if len(row) != len(self.titles):
                raise ValueError("Row length does not match number of titles.")

        for title, column in zip(self.titles, zip(*data)):
            self.replace_column(title, list(column))

    @staticmethod
    def generate_random_sensitive() -> int:
        return randint(1, 100000)

    def initialize_sensitive_column(self):
        """
        Initializes the sensitive column with random values.
        """
        m, _ = self.shape
        self._sensitive = [Table.generate_random_sensitive() for _ in range(m)]

    @staticmethod
    def create_k_anonymous_table(
        number_of_columns: int,
        titles: List[str] = [],
        k_anonymous: int = 2,
        seed_value: Optional[int] = None,
    ) -> "Table":
        """
        Initializes the Table with the given data.
        """
        if number_of_columns < Table.DEFAULT_COLS:
            raise ValueError(
                f"Number of columns must be at least {Table.DEFAULT_COLS}."
            )

        table = Table.empty(seed_value)
        table._titles = titles
        table.table = {title: [] for title in table.titles}

        cols = max(number_of_columns, Table.DEFAULT_COLS)
        table.initialize_k_anonymous_table(cols, k_anonymous)
        table.initialize_sensitive_column()

        return table

    def initialize_k_anonymous_table(self, number_of_columns: int, k: int = 2):
        """
        Initializes the table with the given data.
        """
        # If no titles are provided, generate default titles.
        if len(self.titles) < number_of_columns:
            for i in range(number_of_columns - len(self.titles)):
                title = self.generate_new_title()
                self._titles.append(title)
                self._initial_titles.append(title)
                self.table[title] = []

        # Generate all unique combinations of the titles
        # and fill the table with k-anonymous data.
        unique_combinations = list(
            product(*((Table.yes(), Table.no(True)) for _ in self.titles))
        )
        data = unique_combinations * k
        shuffle(data)

        # Fill the table with the generated data.
        # use the `replace_column` method to ensure titles are added correctly.
        for title, column in zip(self.titles, zip(*data)):
            self.replace_column(title, list(column))

    def __getitem__(
        self, title: str
    ) -> Union[List[str], List[date], List[int], List[float]]:
        """
        Returns the data for the given title.
        """
        return self.table[title]

    @staticmethod
    def yes() -> str:
        """
        Return the matching binary value of the column.
        """
        return "1"

    @staticmethod
    def no(random: bool = False) -> str:
        """
        Return the unmatching binary value of the column.
        """
        if random:
            n = randint(2, 3)
            return f"{n}"

        return "0"

    @property
    def titles(self) -> List[str]:
        """
        Returns the titles of the table.
        """
        return self._titles

    @property
    def initial_titles(self) -> List[str]:
        """
        Returns the initial titles of the table.
        These are the titles that were set when the table was created.
        """
        return self._initial_titles

    @property
    def shape(self) -> tuple[int, int]:
        """
        Returns the shape of the table.
        (rows, columns)
        """
        return (len(self.table[self.titles[0]]), len(self.titles))

    def generate_new_title(self) -> str:
        """
        Generates a new title.
        """
        return f"column_{len(self.titles)}"

    def add_column(
        self, title: str, column: Union[List[str], List[date], List[int], List[float]]
    ):
        """
        Adds a new column to the table.
        """
        if title in self.table:
            raise Exception("Column already exists.")

        self._titles.append(title)
        self.table[title] = column

    def replace_column(
        self, title: str, column: Union[List[str], List[date], List[int], List[float]]
    ):
        """
        Replaces an existing column in the table.
        """
        if title not in self.table:
            raise Exception("Column does not exist.")

        self.table[title] = column

    def add_row(self, row: Union[List[str], List[date], List[int], List[float]]):
        """"""
        if len(row) != self.shape[1]:
            raise Exception("")

        for i, title in enumerate(self.titles):
            self.table[title].append(row[i])

        self._sensitive.append(Table.generate_random_sensitive())

    def show(self):
        """
        Return a pretty print string of the table.
        """
        data = zip(*self.table.values(), self._sensitive)
        titles = self.titles + [self._sensitive_column_name]
        return tabulate(data, headers=titles, tablefmt="grid")

    @staticmethod
    def empty(seed_value: Optional[int] = None) -> "Table":
        """
        Returns an empty table with default columns.
        """
        return Table([], [], seed_value)

    @property
    def sensitive(self) -> List[int]:
        """
        Returns the sensitive column of the table.
        """
        return self._sensitive

    def set_sensitive_column(self, column: List[int]):
        """
        Sets the sensitive column in the table.
        """
        self._sensitive = column

    @property
    def sensitive_column_name(self) -> str:
        """
        Returns the name of the sensitive column.
        """
        return self._sensitive_column_name

    def set_sensitive_column_name(self, name: str):
        """
        Sets the name of the sensitive column.
        """
        self._sensitive_column_name = name

    def initialize_n_records_table(self, n: int, population_value: float):
        """
        Initializes the table with n records.
        """
        # If no titles are provided, generate default titles.
        if len(self.titles) < self.DEFAULT_COLS:
            for _ in range(self.DEFAULT_COLS - len(self.titles)):
                title = self.generate_new_title()
                self._titles.append(title)
                self._initial_titles.append(title)
                self.table[title] = []

        for title in self.titles:
            positive_indexs = sample(range(n), round(n * population_value))
            column = [
                Table.yes() if i in positive_indexs else Table.no(True)
                for i in range(n)
            ]
            self.replace_column(title, column)

    @staticmethod
    def create_table_with_n_records(
        n: int,
        population_value: float,
        titles: List[str] = [],
        seed_value: Optional[int] = None,
    ) -> "Table":
        """
        Initializes the Table with the given data.
        """
        table = Table.empty(seed_value)
        table._titles = titles
        table.table = {title: [] for title in table.titles}

        table.initialize_n_records_table(n, population_value)
        table.initialize_sensitive_column()

        return table

    def copy(self) -> "Table":
        """
        Returns a copy of the table.
        """
        new_table = Table(
            self.titles.copy(), [], self._seed if hasattr(self, "_seed") else None
        )
        new_table.table = {title: column.copy() for title, column in self.table.items()}
        new_table._sensitive = self._sensitive.copy()
        new_table._sensitive_column_name = self._sensitive_column_name
        new_table._initial_titles = self._initial_titles.copy()
        return new_table
