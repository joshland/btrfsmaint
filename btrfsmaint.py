#!/usr/bin/env python3

# btrfsmaint.py -- periodic maintenance for btrfs filesystems
# Copyright(c) 2016 Joshua M. Schmidlkofer <joshland@protonmail.com>
# Released under GPLv2.0 (See LICENSE for details)

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from docopt import docopt
import os, sys, subprocess, time, re

PYTHON3 = sys.version_info[0] == 3
DEBUG=False
INTERACTIVE=False
VERSION = "0.3"
USAGE   = """
Usage: btrfsmaint.py [-d] [-i] [-t] ( <filesystem> [<filesystem>...]| -a )

  -? --help       show this
  -d              debug printout
  -i              Interactive
  -t              Only test and show what would have happened.
  -a              Run for all Filesystems
  <filesystem>    Mountpoint of the BTRFS filesystem.
"""

scrubStopped = [
    re.compile(r"scrub.started.at.+and.was.aborted", re.I|re.M),
    re.compile(r"scrub.started.at.+and.finished.after", re.I|re.M),
    re.compile(r"no.stats.available", re.I|re.M),
    ]

scrubRunning = [
    re.compile(r"scrub.started.*running.for", re.I|re.M),
    ]

def debug(msg):
    global DEBUG
    
    if DEBUG:
        sys.stderr.write("%s\n" % msg)
        sys.stderr.flush()
        pass
    
    return True
        

def _btrfsScrubStatus(volume):
    '''
    Execute 'btrfs scrub status <volume>' 
    
    return output from btrfs scrub status
    '''
    
    retval = subprocess.Popen(['btrfs', 'scrub', 'status', volume], stdout=subprocess.PIPE).communicate()[0]
    if PYTHON3: retval = retval.decode('utf-8')
    retval = retval.strip()
    debug("btrfs scrub status:\n%s" % retval)
    return retval

def _btrfsBalanceRetval(volume):
    '''
    Execute 'btrfs balance status <volume>' 
    
    return output from btrfs balance status
    '''
    handle = subprocess.Popen(['btrfs', 'balance', 'status', volume], stdout=subprocess.PIPE)
    handle.wait()
    retval = handle.returncode
    debug("btrfs balance status returned: %d" % retval)
    return retval

def _execute(cmdline, log = debug, debug = debug):
    '''
    run a command!
    '''
    stderr = ""
    stdout =""
    cmd = cmdline.split(" ")
    debug("cmd execute: %s" % str(cmd))
    handle = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while 1:
        time.sleep(0.1)
        handle.poll()
        response = handle.communicate()
        if PYTHON3:
            out = response[0].decode('utf-8')
            try:
                err = response[1].decode('utf-8')
            except AttributeError:
                err = ""
                pass
        else:
            out = response[0]
            try:
                err = response[1]
            except AttributeError:
                err = ""
                pass
            pass
        
        stdout   += out
        stderr   += err
        log(out)
        if len(err): debug('debug: %s' % err)
        if handle.returncode != None:
            break
        continue

    retval = "%s\n%s" % (stdout, stderr)
    retval = retval.strip()
    debug("cmd returns (%d): \n%s" % (handle.returncode, retval))
    return retval

def ScrubIsRunning(output):
    '''
    check brtfs scrub status vol output for signals
    '''
    Running = "Running"
    Stopped = "Stopped"
    scrub   = None

    for x in scrubRunning:
        results = x.search(output)
        if results:
            scrub = Running
            break
        continue

    for x in scrubStopped:
        results = x.search(output)
        if results:
            if scrub == Running:
                raise WtfIsHappeningHere
            scrub = Stopped
            break
        continue

    if Running == scrub:
        retval = True
    elif Stopped == scrub:
        retval = False
    else:
        debug("false achieved without a match")
        debug("%s" % str(output))
        retval = False
    return retval


def InteractiveRun(cmd):
    '''
    run 'cmd' interactively, giving feedback as it happens
    '''
    def logmessage(msg):
        print(msg)
        return True
    _execute(cmd, log = logmessage, debug = debug)
    return True

def LoggerRun(cmd):
    '''
    run 'cmd', log important messages
    '''
    def logmessage(msg):
        
        return True
    print("UNIMPLEMENTED (use -i): %s" % cmd)
    return True

def TestRun(cmd):
    '''
    run 'cmd', log important messages
    '''
    def logmessage(msg):
        
        return True
    print("WOULD: %s" % cmd)
    return True

def locateBtrfs():
    '''
    local all BTRFS filesystems
    '''
    retval = []
    filesystems = {}
    
    contents = open("/proc/mounts", "r").read()
    for x in contents.split("\n"):
        if x.find(" btrfs ") < 0: continue
        f = x.split(" ")
        if len(f) < 3: continue
        if f[2] != 'btrfs': continue
        if f[1] in retval: continue
        try:
            filesystems[f[0]].append(f[1])
        except KeyError:
            filesystems[f[0]] = [ f[1], ]
            pass
        continue

    retval = [ filesystems[x][0] for x in filesystems.keys() ]
    return retval

def Maintain(fs):
    '''
    execute maintenance steps for [fs]
    '''
    for x in range(2):
        scrubrun = _btrfsScrubStatus(fs)
        if ScrubIsRunning(scrubrun):
            print("Error: Existing Scrub Running.")
            sys.exit(1)
        elif _btrfsBalanceRetval(fs):
            print("Error: Existing Balance Running.")
            sys.exit(1)
        continue

    ### Balance Metadata
    run("btrfs balance start -musage=0 -v %s" % fs)
    if ScrubIsRunning(_btrfsScrubStatus(fs)) or _btrfsBalanceRetval(fs):
        print("Error: Existing Scrub or Balance Running.")
        sys.exit(1)
        pass
    run("btrfs balance start -musage=20 -v %s" % fs)
    if ScrubIsRunning(_btrfsScrubStatus(fs)) or _btrfsBalanceRetval(fs):
        print("Error: Existing Scrub or Balance Running.")
        sys.exit(1)
        pass
    ### Balance Data
    run("btrfs balance start -dusage=0 -v %s" % fs)
    if ScrubIsRunning(_btrfsScrubStatus(fs)) or _btrfsBalanceRetval(fs):
        print("Error: Existing Scrub or Balance Running.")
        sys.exit(1)
        pass
    run("btrfs balance start -dusage=20 -v %s" % fs)
    if ScrubIsRunning(_btrfsScrubStatus(fs)) or _btrfsBalanceRetval(fs):
        print("Error: Existing Scrub or Balance Running.")
        sys.exit(1)
        pass
    
    ### And now we do scrub. Note that scrub can fail with "no space left
    ### on device" if you're very out of balance.
    #logger -s "Starting scrub of $mountpoint" >&2
    #echo btrfs scrub start -Bd $mountpoint
    run("ionice -c 3 nice -10 btrfs scrub start -Bd %s" % fs)
    return True

def Main():
    global DEBUG, run, INTERACTIVE
    
    args = docopt(USAGE, help=True, version='BTRFS Maintainer - %s' % VERSION)
    
    if args['-d']:
        DEBUG=True
        pass
    
    if args['-i']:
        INTERACTIVE=True
        run = InteractiveRun
    else:
        INTERACTIVE=False
        run = LoggerRun
        pass

    ## -t is the final arbiter - Cliff warned me that docopt was inflexible.
    if args['-t']:
        run = TestRun

    debug(args)

    if args['-a']:
        # locate filesystems
        fslist = locateBtrfs()
    else:
        fslist = args['<filesystem>']
        pass
    
    for fs in fslist:
        Maintain(fs)
        continue

    return True

if __name__ == "__main__":
    sys.exit(Main())
