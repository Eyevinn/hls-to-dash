#!/bin/bash
function install_deps {
    pip install -r requirements-dev.txt
}

function run {
    PYTHONPATH=. py.test -vv --cov-report term-missing --cov hls2dash tests/
}

function main {
    install_deps
    run
    retval=$?
    return "$retval"
}

if [ -z "$1" ]; then
    main
else
    $@
fi
