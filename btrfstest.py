#!/usr/bin/env python3

import sys, os
import btrfsmaint
from btrfsmaint import ScrubIsRunning, locateBtrfs

btrfsmaint.DEBUG = True

testspath = "./tests"

def runTests():
    for filename in os.listdir(testspath):
        testfile = os.path.join(testspath, filename)
        if filename.find('true') >= 0:
            print ("Expect: True\n  %s" % ScrubIsRunning(open(testfile, 'r').read()))
            continue
        if filename.find('false') >= 0:
            print ("Expect: False\n  %s" % (ScrubIsRunning(open(testfile, 'r').read())))
            continue
        
        continue

    return True

def checkMount():
    ''' test locateBtrfs '''
    print(locateBtrfs())

if __name__ == "__main__":
    runTests()
    checkMount()
    sys.exit(0)
