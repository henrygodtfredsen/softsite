"""Assessor Parcel Number (APN) handling.

Every APN is stored as 8 plain digits (e.g. "09708058") so records from the
City ("097-08-058"), County ("09708058"), and State ("06085_09708058") join
cleanly. Anything that doesn't clean up to exactly 8 digits returns None; it is
never guessed."""

from __future__ import annotations

import re

_DASHED = re.compile(r"(\d{3})[-\s](\d{2})[-\s](\d{3})")
_FIPS_PREFIX = re.compile(r"^06085[_-]")  # Santa Clara County FIPS code
_FLOAT_SUFFIX = re.compile(r"\.0+$")


def normalize_apn(raw: object) -> str | None:
    if raw is None:
        return None
    s = _FIPS_PREFIX.sub("", str(raw).strip())
    if not s:
        return None
    if m := _DASHED.fullmatch(s):
        return "".join(m.groups())
    s = _FLOAT_SUFFIX.sub("", s)  # "9708058.0" from a spreadsheet
    if re.fullmatch(r"\d{8}", s):
        return s
    if re.fullmatch(r"\d{7}", s):
        # A purely numeric 7-digit value lost its leading zero (spreadsheets do this).
        return "0" + s
    return None


def format_apn(apn: str) -> str:
    """'09708058' -> '097-08-058'."""
    if not re.fullmatch(r"\d{8}", apn):
        raise ValueError(f"not a normalized APN: {apn!r}")
    return f"{apn[:3]}-{apn[3:5]}-{apn[5:]}"


_LIST_TOKEN = re.compile(r"(\d{3})-(\d{2})-(\d{3})|(?<![\w-])-(\d{2,3})\b")


def parse_apn_list(text: str | None) -> list[str]:
    """Pull every APN out of free text, including the shorthand used in CEQA
    filings: 'APNs 097-01-073, -039; 104-01-102' -> 09701073, 09701039, 10401102.
    A short form like '-039' or '-41' reuses the book and page of the APN before it."""
    if not text:
        return []
    found: list[str] = []
    book_page: str | None = None
    for m in _LIST_TOKEN.finditer(text):
        if m.group(1):
            book_page = m.group(1) + m.group(2)
            apn = book_page + m.group(3)
        elif book_page is not None:
            apn = book_page + m.group(4).zfill(3)
        else:
            continue
        if apn not in found:
            found.append(apn)
    return found
