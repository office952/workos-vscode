"""Company working calendar — code-only, factual RO legal holidays.

Firm schedule (Owner): Mon–Fri, 8 hours/day; Sat–Sun closed; legal holidays off.
No invented util %; no client tariff. Capacity/feasibility stays separate.
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import FrozenSet, Iterable, List, Set

WORK_HOURS_PER_DAY = 8.0
WORKING_WEEKDAYS: FrozenSet[int] = frozenset({0, 1, 2, 3, 4})  # Mon–Fri

# Official Romanian non-working public holidays (Labor Code Art. 139 + movable Orthodox).
# Sources: timeanddate.com/holidays/romania, Wikipedia "Public holidays in Romania".
# Years covered: 2025–2027. Extend factually when a new year is needed — do not invent.
_RO_PUBLIC_HOLIDAYS: FrozenSet[date] = frozenset(
    {
        # 2025
        date(2025, 1, 1),
        date(2025, 1, 2),
        date(2025, 1, 6),
        date(2025, 1, 7),
        date(2025, 1, 24),
        date(2025, 4, 18),  # Orthodox Good Friday
        date(2025, 4, 20),  # Orthodox Easter
        date(2025, 4, 21),  # Orthodox Easter Monday
        date(2025, 5, 1),
        date(2025, 6, 1),
        date(2025, 6, 8),  # Orthodox Pentecost
        date(2025, 6, 9),  # Orthodox Pentecost Monday
        date(2025, 8, 15),
        date(2025, 11, 30),
        date(2025, 12, 1),
        date(2025, 12, 25),
        date(2025, 12, 26),
        # 2026
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 6),
        date(2026, 1, 7),
        date(2026, 1, 24),
        date(2026, 4, 10),  # Orthodox Good Friday
        date(2026, 4, 12),  # Orthodox Easter
        date(2026, 4, 13),  # Orthodox Easter Monday
        date(2026, 5, 1),
        date(2026, 5, 31),  # Orthodox Pentecost
        date(2026, 6, 1),  # Children's Day + Pentecost Monday
        date(2026, 8, 15),
        date(2026, 11, 30),
        date(2026, 12, 1),
        date(2026, 12, 25),
        date(2026, 12, 26),
        # 2027
        date(2027, 1, 1),
        date(2027, 1, 2),
        date(2027, 1, 6),
        date(2027, 1, 7),
        date(2027, 1, 24),
        date(2027, 4, 30),  # Orthodox Good Friday
        date(2027, 5, 1),  # Labour Day (also overlaps Easter weekend context)
        date(2027, 5, 2),  # Orthodox Easter
        date(2027, 5, 3),  # Orthodox Easter Monday
        date(2027, 6, 1),
        date(2027, 6, 20),  # Orthodox Pentecost
        date(2027, 6, 21),  # Orthodox Pentecost Monday
        date(2027, 8, 15),
        date(2027, 11, 30),
        date(2027, 12, 1),
        date(2027, 12, 25),
        date(2027, 12, 26),
    }
)


def is_public_holiday(day: date) -> bool:
    return day in _RO_PUBLIC_HOLIDAYS


def is_company_workday(day: date) -> bool:
    """True for Mon–Fri that are not RO public holidays."""
    return day.weekday() in WORKING_WEEKDAYS and not is_public_holiday(day)


def month_bounds(year: int, month: int) -> tuple[date, date]:
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def company_workdays_in_range(start_date: date, end_date: date) -> List[date]:
    if end_date < start_date:
        return []
    days: List[date] = []
    current = start_date
    while current <= end_date:
        if is_company_workday(current):
            days.append(current)
        current = date.fromordinal(current.toordinal() + 1)
    return days


def count_company_workdays(start_date: date, end_date: date) -> int:
    return len(company_workdays_in_range(start_date, end_date))


def company_workdays_in_month(year: int, month: int) -> List[date]:
    start, end = month_bounds(year, month)
    return company_workdays_in_range(start, end)


def count_company_workdays_in_month(year: int, month: int) -> int:
    return len(company_workdays_in_month(year, month))


def holidays_in_month(year: int, month: int) -> List[date]:
    start, end = month_bounds(year, month)
    return sorted(d for d in _RO_PUBLIC_HOLIDAYS if start <= d <= end)


def standard_productive_hours_for_month(year: int, month: int) -> float:
    """Baseline firm productive hours for one FTE in the month (before leave)."""
    return count_company_workdays_in_month(year, month) * WORK_HOURS_PER_DAY


def public_holidays_covering(years: Iterable[int]) -> Set[date]:
    year_set = set(years)
    return {d for d in _RO_PUBLIC_HOLIDAYS if d.year in year_set}
