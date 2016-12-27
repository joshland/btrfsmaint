#!/bin/bash

function fail(){
		printf "$*"
		exit
}

for CMD in python2 python3 pypy3; do
		echo "Testing ${CMD}"
		${CMD} -c "import docopt"                  && echo "  docopt - ok." || fail "${CMD} must have docopt installed"
		${CMD} btrfsmaint.py --help  &> /dev/null  && echo "  launch - ok." || fail "${CMD} --help failed!"
		OUTPUT=$(${CMD} btrfstest.py)              && echo "  tests  - ok."  || fail "${CMD} failed!\n${OUTPUT}"
		done
