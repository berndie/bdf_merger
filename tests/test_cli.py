"""Tests for the commandline interface."""
import os
import subprocess
import sys

import pytest

from tests import TestConfig, build_folder, TestData
from tests.test_merger import TestMerger


@pytest.mark.usefixtures(build_folder.__name__)
class TestCLI:
    """Test the commandline interface."""

    def test_normal_working(self):
        """Test the normal working of the CLI."""
        new_path = os.path.join(TestConfig.build_folder, "cli_test.bdf")
        subprocess.call(
            [
                sys.executable,
                TestConfig.cli_file,
                "--out",
                new_path,
                TestData.bdf_256,
                TestData.bdf_256,
            ]
        )
        TestMerger()._test_new_file(new_path)
