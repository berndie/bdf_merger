"""Tests for the bdf merger tool."""
import os
import shutil

import pytest


class TestData:
    """Paths to data for testing.

    BDF files were taken from https://www.biosemi.com/download/BDFtestfiles.zip
    """

    data_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data"
    )
    bdf_2048 = os.path.join(data_folder, "Newtest17-2048.bdf")
    bdf_256 = os.path.join(data_folder, "Newtest17-256.bdf")


class TestConfig:
    """Special config for testing."""

    root_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    build_folder = os.path.join(root_folder, "build")
    cli_file = os.path.join(root_folder, "bdf_merger.py")


@pytest.fixture
def build_folder():
    """Create and cleanup the build folder for testing."""
    shutil.rmtree(TestConfig.build_folder, ignore_errors=True)
    os.makedirs(TestConfig.build_folder, exist_ok=True)
    yield
    shutil.rmtree(TestConfig.build_folder)
