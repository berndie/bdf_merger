#!/bin/bash

ROOT=$(git rev-parse --show-toplevel)
cd $ROOT
mkdir -p ${ROOT}/test_reports
pytest tests --cov=bdf_merger  --cov-report=xml:coverage.xml -vvv
