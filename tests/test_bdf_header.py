"""Tests for the BDFHeader."""
import time
import datetime

import pytest

from bdf_merger import BDFHeader
from tests import TestData


class TestBDFHeader:
    """Tests for the BDFHeader."""

    def test_attributes(self):
        """Test the attributes of the BDFHeader."""
        attributes = {}
        header = BDFHeader.from_path(TestData.bdf_256)

        for key in BDFHeader.MAPPING.keys():
            attributes[key] = getattr(header, key)
        assert attributes == {
            "identification_code": b"\xffBIOSEMI",
            "subject_identification": "",
            "local_recording_identification": "",
            "start_date": datetime.date(year=2001, month=11, day=5),
            "start_time": time.strptime(
                "19:38:42",
                "%H:%M:%S",
            ),
            "bytes_in_header": 4608,
            "data_format_version": "24BIT",
            "nb_data_records": 60,
            "data_duration": 1,
            "nb_channels": 17,
            "channel_labels": [
                "A1",
                "A2",
                "A3",
                "A4",
                "A5",
                "A6",
                "A7",
                "A8",
                "A9",
                "A10",
                "A11",
                "A12",
                "A13",
                "A14",
                "A15",
                "A16",
                "Status",
            ],
            "transducer_types": [
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "ActiveElectrode,pintype",
                "TriggersandStatus",
            ],
            "dimensions": [
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "uV",
                "Boolean",
            ],
            "min_dimensions": [
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -262144,
                -8388608,
            ],
            "max_dimensions": [
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                262144,
                8388607,
            ],
            "min_digital": [
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
                -8388608,
            ],
            "max_digital": [
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
                8388607,
            ],
            "prefiltering": [
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "HP:DC;LP:113Hz",
                "Nofiltering",
            ],
            "samples_per_record": [
                256,
                256,
                256,
                256,
                256,
                256,
                256,
                256,
                256,
                256,
                256,
                256,
                256,
                256,
                256,
                256,
                256,
            ],
            "reserved": [
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
            ],
        }

    def test_concatenate(self):
        """Test the normal working of the concatenate method."""
        header = BDFHeader.from_path(TestData.bdf_256)
        header2 = BDFHeader.from_path(TestData.bdf_256)
        assert header.nb_data_records == 60
        assert header.data_duration == 1
        assert header2.nb_data_records == 60
        assert header2.data_duration == 1
        assert (header.nb_channels + 1) * 256 == header.bytes_in_header
        header.concatenate(header2)
        assert (header.nb_channels + 1) * 256 == header.bytes_in_header
        assert header.nb_data_records == 120
        assert header.data_duration == 2
        assert header2.nb_data_records == 60
        assert header2.data_duration == 1
        header2.max_dimensions = [99999999] * header2.nb_channels
        header2.min_dimensions = [-9999999] * header2.nb_channels
        header2.max_digital = [99999999] * header2.nb_channels
        header2.min_digital = [-9999999] * header2.nb_channels
        header.concatenate(header2)
        assert header.nb_data_records == 180
        assert header.data_duration == 3
        assert header.max_dimensions == [99999999] * header2.nb_channels
        assert header.min_dimensions == [-9999999] * header2.nb_channels
        assert header.max_digital == [99999999] * header2.nb_channels
        assert header.min_digital == [-9999999] * header2.nb_channels
        assert (header.nb_channels + 1) * 256 == header.bytes_in_header

    def test_concatenate_errors(self):
        """Test that concatenation incompatible BDFHeaders raises an error."""
        header = BDFHeader.from_path(TestData.bdf_2048)
        header2 = BDFHeader.from_path(TestData.bdf_256)
        with pytest.raises(ValueError):
            header.concatenate(header2)

    def test_equality(self):
        """Test that 2 BDFHeaders are equal."""
        header = BDFHeader.from_path(TestData.bdf_2048)
        header2 = BDFHeader.from_path(TestData.bdf_256)

        assert header != header2
        assert header == header
