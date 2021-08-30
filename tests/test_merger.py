"""Merger for BDF files."""
import os
from pathlib import Path
from typing import Union

import pytest

from bdf_merger import Merger, BDFHeader
from tests import TestData, TestConfig, build_folder


@pytest.mark.usefixtures(build_folder.__name__)
class TestMerger:
    """Tests for the Merger class."""

    def test_singlethreaded(self):
        """Test the single-threaded working of the Merger."""
        self._test_merger(
            Merger(use_multiprocessing=False), "singlethreaded.bdf"
        )

    def test_multipprocessing(self):
        """Test the multiprocessing working of the Merger."""
        self._test_merger(
            Merger(use_multiprocessing=True), "multiprocessing.bdf"
        )

    def test_invalid_chunk_size(self):
        """Test that an impossible chunk size throws an error."""
        with pytest.raises(ValueError):
            Merger(chunk_size=-1234)
        with pytest.raises(ValueError):
            Merger(chunk_size=0)

    def test_full_read_chunk_size(self):
        """Test that the whole file can be read in one chunk."""
        self._test_merger(Merger(chunk_size=None), "in_one_go.bdf")

    def test_small_chunk_size(self):
        """Test that an arbitray chunk_size can be chosen."""
        self._test_merger(
            Merger(chunk_size=312, use_multiprocessing=True),
            "small_chunks.bdf",
        )

    def _test_merger(self, merger: Merger, test_filename: Union[str, Path]):
        """Test the merger.

        Parameters
        ----------
        merger : Merger
            Merger object to test
        test_filename : Union[str, Path]
            Filename for the newly merged BDF file
        """
        test_path = os.path.join(TestConfig.build_folder, test_filename)

        merger.merge([TestData.bdf_256, TestData.bdf_256], test_path)
        self._test_new_file(test_path)

    def _test_new_file(self, test_path):
        header = BDFHeader.from_path(test_path)
        assert (header.nb_channels + 1) * 256 == header.bytes_in_header
        assert header.nb_data_records == 120
        assert header.data_duration == 2
        with open(TestData.bdf_256, "rb") as fp:
            temp_header = BDFHeader.from_fp(fp)
            fp.seek(temp_header.bytes_in_header)
            temp_data = fp.read()

        with open(test_path, "rb") as fp:
            total_data_length = (
                sum(header.samples_per_record) * 3 * header.nb_data_records
            )
            assert total_data_length == 1566720
            fp.seek(header.bytes_in_header)
            data = fp.read()
            assert total_data_length == len(data)
            assert temp_data * 2 == data
