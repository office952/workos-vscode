from __future__ import annotations

from html import escape
from typing import Iterable


def escape_html_text(value: object) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=True)


def escape_html_attr(value: object) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=True)


def safe_join_html_lines(values: Iterable[object], separator: str = "<br>") -> str:
    return separator.join(escape_html_text(value) for value in values)
