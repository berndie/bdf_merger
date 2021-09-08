BDF merger tool
===============

![CI workflow](https://github.com/berndie/bdf_merger/actions/workflows/ci.yaml/badge.svg)
[![Python](https://img.shields.io/badge/Python_version-3.0+-blue)](https://www.python.org/)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![codecov](https://codecov.io/gh/berndie/bdf_merger/branch/master/graph/badge.svg?token=1QAWJ4B2Y1)](https://codecov.io/gh/berndie/bdf_merger)

This is a python3 tool for merging [EEG measurement files in BDF format](https://www.biosemi.com/faq/file_format.htm).


This tool is __Extremely portable__: with just one file ([bdf_merger.py](./bdf_merger.py)) and Python 3 (all versions), you can start merging BDF files! No external dependencies!


## Usage

```
usage: bdf_merger.py [-h] --out OUT [--disable-multiprocessing]
                     [--chunk-size CHUNK_SIZE]
                     bdfs [bdfs ...]

Merge 2 (or more) BDF files

positional arguments:
  bdfs                  BDF's to merge

optional arguments:
  -h, --help            show this help message and exit
  --out OUT             Output BDF file
  --disable-multiprocessing
                        Disable multiprocessing for merging
  --chunk-size CHUNK_SIZE
                        Size of the chunks to read. Default is 1 record at a
                        time
```

## Development

If you want to contribute, you'll have to install the requirements for testing:
```bash
pip3 install -r development_requirements.txt
```

Continuous integration is enabled on this repository and your fork will not
be accepted unless all checks (as defined below) are OK. Github workflows are
used (see [CI](./.github/workflows/ci.yaml)).

### Code style

[flake8](https://github.com/pycqa/flake8) and 
[flake8-docstrings](https://gitlab.com/pycqa/flake8-docstrings) are used to 
check your code for compliance.
To help with autoformatting, [black]() is used. The script in 
[scripts/lint.sh](./scripts/lint.sh) can also be used for linting purposes.

### Testing

[pytest](https://pytest.org) will be used to run the tests in [tests](./tests).
[tox](https://tox.readthedocs.io/en/latest/) will be used to check all the 
individual Python3 versions.

For coverage [pytest-cov](https://github.com/pytest-dev/pytest-cov) is used.



