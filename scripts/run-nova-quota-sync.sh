#!/usr/bin/env bash

command -v pip >/dev/null 2>&1 || { echo >&2 "pip not installed"; exit 1; }
command -v virtualenv >/dev/null 2>&1 || { echo >&2 "virtualenv not installed"; exit 1; }

if [[ $# -lt 1 ]]; then

    echo usage: $0 CONFIGURATION
    exit 1

fi

configuration=$1
shift

if [[ ! -e $configuration ]]; then

    echo configuration file $configuration does not exist
    exit 1

else

    source $configuration

fi

if [[ ! -e .venv ]]; then

    virtualenv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

else

    source .venv/bin/activate

fi

python nova/quota-sync.py --auto-sync
