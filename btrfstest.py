#!/usr/bin/env python3

import sys, os
import btrfsmaint
from btrfsmaint import ScrubIsRunning

btrfsmaint.DEBUG = True

def runTests():
    for x in os.listdir('.'):
        if x.find('btrfsmaint-test') == -1: continue
        if x.find('true') >= 0:
            print ("Expect: True\n  %s" % ScrubIsRunning(open(x, 'r').read()))
            continue
        if x.find('false') >= 0:
            print ("Expect: False\n  %s" % (ScrubIsRunning(open(x, 'r').read())))
            continue
        
        continue


if __name__ == "__main__":
    runTests()
    sys.exit(0)
