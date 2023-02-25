"""Test utilities in the `lib` module."""
from scripts.lib import scraper


def test_query_fields() -> None:
    """Test that QUERY_FIELDS are extracted correctly."""
    assert scraper.QUERY_FIELDS == ["date_from", "date_to"]
