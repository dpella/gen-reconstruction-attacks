from datetime import date
from dateutil.relativedelta import relativedelta

from src.table.condition.base import ICondition


class DateRange(ICondition[date]):
    """
    A condition that checks if a date falls within a range.
    The range is specified in months relative to a start date.
    """
    def __init__(self, column: str, start_months: int, end_months: int, base_date: date):
        self._column = column
        self._start_months = start_months
        self._end_months = end_months
        self._base_date = base_date
        self._start_date = base_date + relativedelta(months=start_months)
        self._end_date = base_date + relativedelta(months=end_months)

    def execute(self, value: date) -> bool:
        """Check if value is within [start_date, end_date)."""
        return self._start_date <= value < self._end_date

    def to_string(self) -> str:
        """Return SQL string representation."""
        return f"{self._column} >= {self._start_date.strftime('%Y-%m-%d')} AND {self._column} < {self._end_date.strftime('%Y-%m-%d')}"
