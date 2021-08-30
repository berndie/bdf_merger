#!/bin/bash

ROOT=$(git rev-parse --show-toplevel)
FIX="false"

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -f|--fix)
      FIX="true"
      shift # past argument
      ;;
    *)    # unknown option
      POSITIONAL+=("$1") # save it in an array for later
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL[@]}" # restore positional parameters

if [[ -n $1 ]]; then
    echo "Last line of file specified as non-opt/last argument:"
    tail -1 "$1"
fi

wd=$(pwd)
cd $ROOT
if [[ "$FIX" == "true" ]]; then
  python3 -m black $ROOT
fi
python3 -m flake8 $ROOT