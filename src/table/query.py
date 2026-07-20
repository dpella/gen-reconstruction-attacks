from typing import Dict, List, TypeVar, Generic, Optional
from abc import ABC, abstractmethod
from datetime import date
from dateutil.relativedelta import relativedelta

from src.common import DEFAULT_DATE, Range, avg
from src.table.table import Table
from src.table.condition import ICondition, EQ, OR, AND, GEQT, LT, DateRange

T = TypeVar("T")
V = TypeVar("V")


class IQuery(Generic[T, V], ABC):
    """
    An interface for a query that can be applied to a table.
    - `T`: The type of the result of the query.
    - `V`: The type of the vector representation of the query result.
    """

    @abstractmethod
    def __call__(self, table: Table) -> T:
        """
        Calls the query on the given table.
        """
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        """
        Returns the title of the query.
        """
        pass

    @property
    @abstractmethod
    def sql(self) -> str:
        """
        Returns the SQL representation of the query.
        """
        pass

    @abstractmethod
    def as_vector(self, table: Table) -> V:
        """
        Converts the query result to a vector representation.
        """
        pass


class SelectQuery(IQuery[float, List[int]]):
    """
    A class that represents a sql `select ...;` query.
    """

    def __init__(self, aggregate: str):
        """
        Initializes the Query with the given title.
        """
        self._aggregate = aggregate
        self._title = "*"

    def __call__(self, table: Table) -> float:
        return avg(table.sensitive)

    @property
    def title(self) -> str:
        return self._title

    @property
    def sql(self) -> str:
        return f"SELECT AVG({self._aggregate}) FROM table;"

    def as_vector(self, table: Table) -> List[int]:
        m, _ = table.shape
        return [1 for _ in range(m)]


class SelectWhereQuery(SelectQuery):
    """
    A class that represents a sql `select ... where ...;` query.
    Uses composable ICondition objects for filtering.
    """

    def __init__(self, aggregate: str, title: str, condition: ICondition):
        """
        Initializes the Query with the given title and condition.
        For backward compatibility, can also accept a value string for equality check.
        """
        self._aggregate = aggregate
        self._title = title
        self._condition = condition

    @classmethod
    def from_value(cls, aggregate: str, title: str, value: str) -> "SelectWhereQuery":
        """
        Factory method for backward compatibility.
        Creates a SelectWhereQuery with an equality condition.
        """
        return cls(aggregate, title, EQ(title, value))

    def __call__(self, table: Table) -> float:
        return avg(
            [
                table.sensitive[i]
                for (i, x) in enumerate(table[self._title])
                if self._condition.execute(x)
            ]
        )

    @property
    def title(self) -> str:
        return self._title

    @property
    def sql(self) -> str:
        return f"SELECT AVG({self._aggregate}) FROM table WHERE {self._condition.to_string()};"

    def as_vector(self, table: Table) -> List[int]:
        return [1 if self._condition.execute(x) else 0 for x in table[self._title]]


class SelectRangeQuery(SelectWhereQuery):
    """
    A class that represents a sql `select ... where (value >= start AND value < end) OR ...;` query.
    Uses composite conditions built from ranges.
    """
    def __init__(self, aggregate: str, title: str, check_set: List[Range]):
        """
        Initializes the Query with the given title and range.
        Builds a composite OR condition from multiple range conditions.
        """
        # Build composite condition: OR of (start <= x < end) for each range
        range_conditions = []
        for start, end in check_set:
            # Each range is: (value >= start) AND (value < end)
            range_cond = AND(
                GEQT(title, start),
                LT(title, end)
            )
            range_conditions.append(range_cond)

        # Combine all ranges with OR
        condition = OR(*range_conditions) if len(range_conditions) > 1 else range_conditions[0]

        # Call parent constructor with the composite condition
        super().__init__(aggregate, title, condition)
        self._check_set = check_set


class SelectDateRangeQuery(SelectWhereQuery):
    """
    A class that represents a sql `select ... where (date between ... and ... or ...);` query.
    Uses composite DateRange conditions for date filtering.
    """

    def __init__(
        self,
        aggregate: str,
        title: str,
        check_set: List[Range],
        start_date: date = DEFAULT_DATE,
    ):
        """
        Initializes the Query with the given title and date range.
        Builds a composite OR condition from multiple date range conditions.
        """
        # Build composite condition: OR of DateRange conditions
        date_range_conditions = []
        for start_months, end_months in check_set:
            date_range_cond = DateRange(title, start_months, end_months, start_date)
            date_range_conditions.append(date_range_cond)

        # Combine all date ranges with OR
        condition = OR(*date_range_conditions) if len(date_range_conditions) > 1 else date_range_conditions[0]

        # Call parent constructor with the composite condition
        super().__init__(aggregate, title, condition)
        self._check_set = check_set
        self._start_date = start_date


class GroupByQuery(IQuery[Dict[str, float], Dict[str, List[int]]]):
    """
    A class that represents a sql `select ... group by ...;` query.
    The condition is for grouping the results by a specific column.
    """

    def __init__(self, aggregate: str, title: str):
        """
        Initializes the Query with the given title.
        """
        self._aggregate = aggregate
        self._title = title

    def __call__(self, table: Table) -> Dict[str, float]:
        vector = self.as_vector(table)
        return {
            k: avg([table._sensitive[i] for i, x in enumerate(v) if x])
            for k, v in vector.items()
        }

    @property
    def title(self) -> str:
        return self._title

    @property
    def sql(self) -> str:
        return f"SELECT {self._title}, AVG({self._aggregate}) FROM table GROUP BY {self._title};"

    def as_vector(self, table: Table) -> Dict[str, List[int]]:
        m, _ = table.shape
        values = table[self._title]

        marks: Dict[str, List[int]] = {}
        for i, v in enumerate(values):
            key = v if isinstance(v, str) else str(v)
            if v not in marks:
                marks[key] = [0 for _ in range(m)]

            marks[key][i] = 1
        return marks
