from __future__ import annotations

import re
from datetime import date


GUJARATI_DIGITS = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")
DATE_PARTS = re.compile(r"^\s*(\d{1,4})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{1,4})\s*$")


def normalize_date(value: str | None) -> str | None:
    """Return an ISO YYYY-MM-DD date for common Indian legal-date formats.

    Documents commonly use DD/MM/YYYY, including Gujarati numerals. A
    four-digit first component is treated as YYYY-MM-DD; otherwise the
    conventional Indian DD/MM/YYYY order is used. Invalid dates are rejected.
    """
    if not value:
        return None
    match = DATE_PARTS.match(value.translate(GUJARATI_DIGITS))
    if not match:
        return None
    first, second, third = (int(part) for part in match.groups())
    if len(match.group(1)) == 4:
        year, month, day = first, second, third
    else:
        day, month, year = first, second, third
        if year < 100:
            year += 2000 if year < 50 else 1900
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None
