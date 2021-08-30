#!/bin/bash

ROOT=$(git rev-parse --show-toplevel)
cd $ROOT
python3 -m pytest $ROOT/tests
