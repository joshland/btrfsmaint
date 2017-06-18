#!/usr/bin/env python3

# btrfsmaint.py -- periodic maintenance for btrfs filesystems
# Copyright(c) 2016 Joshua M. Schmidlkofer <joshland@protonmail.com>
# Released under GPLv2.0 (See LICENSE for details)

from __future__ import print_function
from __future__ import unicode_literals


import click
import os, sys, subprocess, time, re
import logging, logging.handlers

from logging.handlers import SysLogHandler

PYTHON3 = sys.version_info[0] == 3
DEBUG   = False
_log    = None
VERSION = "0.4"
USAGE   = """
Usage: btrfsmaint.py [-d] [-i] [-t] ( <filesystem> [<filesystem>...]| -a )

  -? --help       show this
  -d              debug printout
  -i              Interactive
  -t              Only test and show what would have happened.
  -a              Run for all Filesystems
  <filesystem>    Mountpoint of the BTRFS filesystem.
"""

MessagesScrubStopped = [
    re.compile(r"scrub.started.at.+and.was.aborted", re.I|re.M),
    re.compile(r"scrub.started.at.+and.finished.after", re.I|re.M),
    re.compile(r"no.stats.available", re.I|re.M),
    ]

MessagesScrubRunning = [
    re.compile(r"scrub.started.*running.for", re.I|re.M),
    ]

def _cmd_btrfsScrubStatus(volume, debug):
    '''
    Execute 'btrfs scrub status <volume>' 
    
    return output from btrfs scrub status
    '''
    
    retval = subprocess.Popen(['btrfs', 'scrub', 'status', volume], stdout=subprocess.PIPE).communicate()[0]
    if PYTHON3: retval = retval.decode('utf-8')
    retval = retval.strip()
    _log.debug("btrfs scrub status:\n%s" % retval)
    return retval

def _cmd_btrfsBalanceRetval(volume, debug):
    '''
    Execute 'btrfs balance status <volume>' 
    
    return output from btrfs balance status
    '''
    handle = subprocess.Popen(['btrfs', 'balance', 'status', volume], stdout=subprocess.PIPE)
    handle.wait()
    retval = handle.returncode
    _log.debug("btrfs balance status returned: %d" % retval)
    return retval

def _cmd_execute(cmdline, debug):
    '''
    run a command!
    '''
    stderr = ""
    stdout =""
    cmd = cmdline.split(" ")
    _log.info("cmd execute: %s" % str(cmd))
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
        _log.info(out)
        if len(err): _log.debug('debug: %s' % err)
        if handle.returncode != None:
            break
        continue

    retval = "%s\n%s" % (stdout, stderr)
    retval = retval.strip()
    _log.debug("cmd returns (%d): \n%s" % (handle.returncode, retval))
    return retval

def ScrubIsRunning(output):
    '''
    check brtfs scrub status vol output for signals
    '''
    Running = "Running"
    Stopped = "Stopped"
    scrub   = None

    for x in MessagesScrubRunning:
        results = x.search(output)
        if results:
            scrub = Running
            break
        continue
    for x in MessagesScrubStopped:
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
        _log.debug("false achieved without a match")
        _log.debug("%s" % str(output))
        retval = False
    return retval


def InteractiveRun(cmd, debug):
    '''
    run 'cmd' interactively, giving feedback as it happens
    '''
    _cmd_execute(cmd, debug = debug)
    return True

def LoggerRun(cmd, debug):
    '''
    run 'cmd', log important messages
    '''
    _cmd_execute(cmd, debug = debug)
    return True

def TestRun(cmd, debug):
    '''
    run 'cmd', log important messages
    '''
    click.echo("WOULD: %s" % cmd)
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

def Maintain(fs, run, scrub, debug):
    '''
    execute maintenance steps for [fs]
    '''
    for x in range(2):
        scrubrun = _cmd_btrfsScrubStatus(fs, debug)
        if ScrubIsRunning(scrubrun):
            click.echo("Error: Existing Scrub Running.")
            sys.exit(1)
        elif _cmd_btrfsBalanceRetval(fs, debug):
            click.echo("Error: Existing Balance Running.")
            sys.exit(1)
        continue
    
    ### Balance Metadata
    run("btrfs balance start -musage=0 -v %s" % fs, debug)
    if ScrubIsRunning(_cmd_btrfsScrubStatus(fs, debug)) or _cmd_btrfsBalanceRetval(fs, debug):
        click.echo("Error: Existing Scrub or Balance Running.")
        sys.exit(1)
        pass
    run("btrfs balance start -musage=20 -v %s" % fs, debug)
    if ScrubIsRunning(_cmd_btrfsScrubStatus(fs, debug)) or _cmd_btrfsBalanceRetval(fs, debug):
        click.echo("Error: Existing Scrub or Balance Running.")
        sys.exit(1)
        pass
    ### Balance Data
    run("btrfs balance start -dusage=0 -v %s" % fs, debug)
    if ScrubIsRunning(_cmd_btrfsScrubStatus(fs, debug)) or _cmd_btrfsBalanceRetval(fs, debug):
        click.echo("Error: Existing Scrub or Balance Running.")
        sys.exit(1)
        pass
    run("btrfs balance start -dusage=20 -v %s" % fs, debug)
    if ScrubIsRunning(_cmd_btrfsScrubStatus(fs, debug)) or _cmd_btrfsBalanceRetval(fs, debug):
        click.echo("Error: Existing Scrub or Balance Running.")
        sys.exit(1)
        pass
    ### Scrub disks
    if scrub: run("ionice -c 3 nice -10 btrfs scrub start -Bd %s" % fs, debug)
    
    return True


@click.command()
@click.option("-a", '--allfs',       is_flag=True,
              help = "Target all filesystems.")
@click.option("-d", '--debug',       is_flag=True,
              help = "Enable debug-mode logging.")
@click.option("-t", '--test',        is_flag=True,
              help = "Test commands, but do not run them.")
@click.option('--silent/--interactive', is_flag=True, default=True,
              help = "Use logging output, or interactive output. (default: silent)")
@click.option("--scrub/--no-scrub",  is_flag=True, default=True,
              help = "Enable/Disable scrubbing. (default: enabled)")
@click.argument('filesystems', default = [])
@click.pass_context
def Main(ctx, silent, debug, test, allfs, scrub, filesystems):
    '''
    perform btrfs filesystem maintenace for one, many or [-a]ll filesystems.
    '''
    global DEBUG, _log
    DEBUG=debug

    if debug:
        click.echo("allfs: %s" % str(allfs))
        click.echo("debug: %s" % str(debug))
        click.echo("silent: %s"  % str(silent))
        click.echo("test: %s"  % str(test))
        click.echo("filesystems: %s" % str(filesystems))
        pass
    
    _log = logging.getLogger()
    if len(filesystems) == 0 and not allfs:
        print("You must either use '-a' or specify a filesystem.")
        print("")
        print(ctx.get_help())
        exit()
        
    if test:     run = TestRun
    elif silent: run = LoggerRun
    else:        run = InteractiveRun
    
    if run == InteractiveRun:
        click.echo("Run is set to Interactive")
        _log.addHandler(SysLogHandler(address="/dev/log"))
        _log.addHandler(logging.StreamHandler(sys.stdout))
    if run == TestRun:
        click.echo("Run is set to Test")
    if run == LoggerRun:
        _log.addHandler(SysLogHandler(address="/dev/log"))
        click.echo("Run is set to Logger")
        pass
    
    if allfs: filesystems = locateBtrfs()
    
    for fs in filesystems:
        Maintain(fs, run, scrub, debug)
        continue
    
    return True

if __name__ == "__main__":
    sys.exit(Main())
