"""Test parsers."""
import time
import datetime

import pytest

from bdf_merger import (
    BytesParser,
    StringParser,
    TimeParser,
    DateParser,
    IntParser,
)


class TestBytesParser:
    """Tests for the BytesParser."""

    def test_from_bytes(self):
        """Test the from_bytes method."""
        parser = BytesParser()
        assert parser.from_bytes(b"123abc   ") == b"123abc"

    def test_to_bytes(self):
        """Test the to_bytes method."""
        parser = BytesParser()
        assert parser.to_bytes(b"123abc", 8) == b"123abc  "

    def test_padding(self):
        """Test the padding byte."""
        parser = BytesParser(padding_byte=b"_")
        assert parser.to_bytes(b"123abc", 8) == b"123abc__"
        assert parser.from_bytes(b"123abc___") == b"123abc"

    def test_invalid_length(self):
        """Test that an error is raised if the bytestring is too long."""
        parser = BytesParser()
        with pytest.raises(ValueError):
            parser.to_bytes(b"123abc", 3)


class TestStringParser:
    """Tests for the StringParser."""

    def test_from_bytes(self):
        """Test the from_bytes method."""
        parser = StringParser()
        assert parser.from_bytes(b"123abc   ") == "123abc"

    def test_to_bytes(self):
        """Test the to_bytes method."""
        parser = StringParser()
        assert parser.to_bytes("123abc", 8) == b"123abc  "

    def test_encoding(self):
        """Test the to_encoding and from_encoding."""
        ascii_parser = StringParser()
        utf8_parser = StringParser(to_encoding="utf-8", from_encoding="utf-8")
        with pytest.raises(UnicodeDecodeError):
            ascii_parser.from_bytes(b"\xf0\x9f\x98\x82")
        assert utf8_parser.from_bytes(b"\xf0\x9f\x98\x82") == "😂"
        with pytest.raises(UnicodeEncodeError):
            ascii_parser.to_bytes("😂", 8)
        # Be careful with unicode/utf-8 and padding: multiple bytes can
        # represent one character
        assert utf8_parser.to_bytes("😂", 8) == b"\xf0\x9f\x98\x82    "


class TestTimeParser:
    """Tests for the TimeParser."""

    def test_from_bytes(self):
        """Test the from_bytes method."""
        parser = TimeParser()
        assert parser.from_bytes(b"12.11.10") == time.strptime(
            "12.11.10", parser.from_format
        )

    def test_to_bytes(self):
        """Test the to_bytes method."""
        parser = TimeParser()
        assert (
            parser.to_bytes(time.strptime("12.11.10", parser.to_format), 8)
            == b"12.11.10"
        )

    def test_format(self):
        """Test the to_format and from_format."""
        parser = TimeParser(to_format="%H|%M|%S", from_format="%H|%M|%S")
        assert parser.from_bytes(b"12|11|10") == time.strptime(
            "12|11|10", parser.from_format
        )
        assert (
            parser.to_bytes(time.strptime("12|11|10", parser.to_format), 8)
            == b"12|11|10"
        )


class TestDateParser:
    """Tests for the TimeParser."""

    def test_from_bytes(self):
        """Test the from_bytes method."""
        parser = DateParser()
        assert parser.from_bytes(b"01.02.03") == datetime.date(
            year=2003, month=2, day=1
        )

    def test_to_bytes(self):
        """Test the to_bytes method."""
        parser = DateParser()
        assert (
            parser.to_bytes(datetime.date(year=2003, month=2, day=1), 8)
            == b"01.02.03"
        )

    def test_format(self):
        """Test the to_format and from_format."""
        parser = DateParser(to_format="%d|%m|%y", from_format="%d|%m|%y")
        assert parser.from_bytes(b"01|02|03") == datetime.date(
            year=2003, month=2, day=1
        )
        assert (
            parser.to_bytes(datetime.date(year=2003, month=2, day=1), 8)
            == b"01|02|03"
        )


class TestIntParser:
    """Tests for the TimeParser."""

    def test_from_bytes(self):
        """Test the from_bytes method."""
        parser = IntParser()
        assert parser.from_bytes(b"00123   ") == 123

    def test_to_bytes(self):
        """Test the to_bytes method."""
        parser = IntParser()
        assert parser.to_bytes(123, 8) == b"123     "
