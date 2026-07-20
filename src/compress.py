"""
This module provides functionality for compressing the information of a table
"""

from datetime import date
from dateutil.relativedelta import relativedelta
from random import randint, uniform
from typing import List, Optional, Tuple, Union, cast

from src.logger import Logger
from src.table.table import Table
from src.table.query import (
    IQuery,
    SelectWhereQuery as Query,
    SelectDateRangeQuery as DateQuery,
    SelectRangeQuery as RangeQuery,
)
from src.common import Range


class Compress:
    """
    A class that compress a table with classifying attributes to
    range value attributes (e.g. timestamps)
    """

    def __init__(self, table: Table):
        self.__table = table
        self.__logger = Logger.get_instance()
        self.__start_date: Optional[date] = None

    def set_columns_to_compress(self, titles: List[str]) -> "Compress":
        """
        Set the columns to compress.
        """
        if any(title not in self.__table.titles for title in titles):
            self.__logger.warning("Some columns are not in the table")
            raise ValueError("Some columns are not in the table")

        self.__titles_to_compress = titles
        return self

    def set_column_title(self, title: str) -> "Compress":
        """
        Set the column compressed title
        """
        self.__compressed_column_title = title
        return self

    def set_interval_length(self, interval_length: int) -> "Compress":
        """
        Set the interval length for the compression.
        """
        self.__interval_length = interval_length
        return self

    def compress_record(
        self, record: List[Tuple[str, str]], initial_range: Range
    ) -> Range:
        """
        Compress a record by converting the specified columns to ranges.
        """
        start, end = initial_range
        for _, v in record:
            if end - start <= 1:
                self.__logger.debug(f"Range {start}-{end} is too small to compress")
                break

            m = (end - start) // 2
            if v == Table.yes():
                start += m
            else:
                end -= m

        self.__logger.debug(f"Compressed record {record} to range {start}-{end}")
        return Range(start, end)

    def set_start_date(self, start_date: date) -> "Compress":
        """
        Set the start date for the compression.
        """
        self.__start_date = start_date
        return self

    def __apply_mutation(
        self, range_column: List[Range]
    ) -> Union[List[str], List[date], List[int], List[float]]:
        """
        Apply the mutation to the new range column.
        """
        value_column = [uniform(start, end - 1) for (start, end) in range_column]

        if self.__start_date:
            return [
                self.__start_date + relativedelta(months=int(v)) for v in value_column
            ]

        return value_column

    def __generate_queries(self, title: str, initial_range: Range) -> List[Query]:
        """
        Generates the queries for the new compressed column.
        """
        start, end = initial_range
        number_of_columns = len(self.__titles_to_compress)
        queries: List[Query] = []
        for i in range(1, number_of_columns + 1):
            m = (end - start) // (2**i)
            check_set = [
                Range(start + j * m, start + (j + 1) * m) for j in range(1, 2**i, 2)
            ]

            if self.__start_date:
                queries.append(
                    DateQuery(
                        self.__table.sensitive_column_name,
                        title,
                        check_set,
                        self.__start_date,
                    )
                )
            else:
                queries.append(
                    RangeQuery(self.__table.sensitive_column_name, title, check_set)
                )

            self.__logger.debug(
                f"Generated query for title {title} with range {start}-{end} and check set {check_set}"
            )

        return queries

    def compress(self, old_queries: List[IQuery]) -> Tuple[Table, List[IQuery]]:
        """
        Compress the table by converting the specified columns to ranges.
        """
        if not self.__titles_to_compress:
            raise ValueError("No columns to compress")

        if self.__table.titles[-1] in self.__titles_to_compress:
            raise ValueError("Last column cannot be compressed")

        n, _ = self.__table.shape
        range_length = (2 ** (len(self.__titles_to_compress))) * self.__interval_length

        new_table = Table.empty()
        new_table.set_sensitive_column_name(self.__table.sensitive_column_name)
        new_table.set_sensitive_column(self.__table.sensitive)
        new_queries: List[IQuery] = []

        for title in self.__table.titles:
            if title not in self.__titles_to_compress:
                new_table.add_column(title, self.__table[title])

        for old in old_queries:
            if old.title not in self.__titles_to_compress:
                new_queries.append(old)

        initial_range = Range(0, range_length)
        new_range_column: List[Range] = []
        new_title = self.__compressed_column_title
        self.__logger.debug(f"Initial range: {initial_range}")

        for i in range(n):
            record = [
                (title, cast(str, self.__table[title][i]))
                for title in self.__titles_to_compress
            ]
            compressed_record = self.compress_record(record, initial_range)
            new_range_column.append(compressed_record)

        applied_mutation = self.__apply_mutation(new_range_column)
        new_table.add_column(new_title, applied_mutation)
        new_queries += self.__generate_queries(new_title, initial_range)

        return new_table, new_queries
