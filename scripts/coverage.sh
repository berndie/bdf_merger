#!/bin/bash

ROOT=`pwd` #$(git rev-parse --show-toplevel)
cd $ROOT
mkdir -p ${ROOT}/test_reports
pytest tests --cov=bdf_merger  --cov-report=xml -vvv

#grep -E -o "TOTAL.+" test_reports/coverage_output | cut -d " " -f 24 > ${ROOT}/test_reports/coverage_percentage
echo $(cat ${ROOT}/test_reports/coverage_percentage)