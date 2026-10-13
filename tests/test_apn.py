import pytest

from pipeline.apn import format_apn, normalize_apn, parse_apn_list


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("097-08-058", "09708058"),      # City GIS
        ("09708058", "09708058"),        # County address points
        ("06085_10404131", "10404131"),  # State SB 6 fips_apn
        ("097 08 058", "09708058"),
        (" 220-31-079 ", "22031079"),
        ("9708058", "09708058"),         # leading zero lost in a spreadsheet
        (9708058, "09708058"),
        ("9708058.0", "09708058"),
    ],
)
def test_normalize_apn_accepts_known_formats(raw, expected):
    assert normalize_apn(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [None, "", "097-08-58", "97-08-058", "0970805812", "APN 097-08-058", "abc", "097-08-0588"],
)
def test_normalize_apn_rejects_anything_else(raw):
    # Never guess: malformed values come back as None so they get logged.
    assert normalize_apn(raw) is None


def test_format_apn_round_trip():
    assert format_apn("09708058") == "097-08-058"
    assert normalize_apn(format_apn("22031079")) == "22031079"
    with pytest.raises(ValueError):
        format_apn("097-08-058")


def test_parse_apn_list_handles_ceqa_shorthand():
    # Real CEQAnet text from the City Place filing (SCH 2014072078).
    text = "APNs 097-01-073, -039; 104-01-102; 104-03-036, -41,-42,-43"
    assert parse_apn_list(text) == [
        "09701073", "09701039", "10401102", "10403036", "10403041", "10403042", "10403043",
    ]


def test_parse_apn_list_simple_and_empty():
    assert parse_apn_list("097-08-058") == ["09708058"]
    assert parse_apn_list("Parcel Number: 230-05-021") == ["23005021"]
    assert parse_apn_list(None) == []
    assert parse_apn_list("no parcel here, call 555-123-4567") == []


def test_parse_apn_list_ignores_shorthand_without_a_preceding_apn():
    assert parse_apn_list("-039 then 104-01-102") == ["10401102"]
