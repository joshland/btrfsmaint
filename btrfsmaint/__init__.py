#!/usr/bin/env python

# btrfsmaint.py -- periodic maintenance for btrfs filesystems
# Copyright(c) 2016 Joshua M. Schmidlkofer <joshland@protonmail.com>
# Released under GPLv2.0 (See LICENSE for details)
from __future__ import print_function

import click
import os, sys, subprocess, time, re
import logging, logging.handlers

from logging.handlers import SysLogHandler

PYTHON3 = sys.version_info[0] == 3
DEBUG   = False
_log    = None
VERSION = "0.5.2"
USAGE   = """
Usage: btrfsmaint.py [-d] [-i] [-t] ( <filesystem> [<filesystem>...]| -a )

  -? --help       show this
  -d              debug printout
  -i              Interactive
  -t              Only test and show what would have happened.
  -a              Run for all Filesystems
  <filesystem>    Mountpoint of the BTRFS filesystem.
"""
LOGROOT="btrfsmaint"

MessagesScrubStopped = [
    re.compile(r"scrub.started.at.+and.was.aborted", re.I|re.M),
    re.compile(r"scrub.started.at.+and.finished.after", re.I|re.M),
    re.compile(r"no.stats.available", re.I|re.M),
    ]

MessagesScrubRunning = [
    re.compile(r"scrub.started.*running.for", re.I|re.M),
    ]

def gatherRetval(results):
    if PYTHON3:
        retval = results.decode('utf-8').strip()
    else:
        retval = results.strip()
        pass
    return retval

def _cmd_btrfsScrubStatus(volume):
    '''
    Execute 'btrfs scrub status <volume>' 
    
    return output from btrfs scrub status
    '''
    log = logging.getLogger("%s.scrub" % LOGROOT)
    log.debug("subprocess start.")
    retval = subprocess.Popen(['btrfs', 'scrub', 'status', volume], stdout=subprocess.PIPE).communicate()[0]
    log.debug("subprocess complete.")
    retval = gatherRetval(retval)
    log.debug("btrfs scrub status:\n%s" % retval)
    return retval

def _cmd_btrfsBalanceRetval(volume):
    '''
    Execute 'btrfs balance status <volume>' 
    
    return output from btrfs balance status
    '''
    log = logging.getLogger("%s.balance" % LOGROOT)
    log.debug("subprocess open")
    handle = subprocess.Popen(['btrfs', 'balance', 'status', volume], stdout=subprocess.PIPE)
    log.debug("subprocess starts")
    handle.wait()
    log.debug("subprocess complete")
    retval = handle.returncode
    log.info("btrfs balance status returned: %d" % retval)
    return retval

def _cmd_execute(cmdline):
    '''
    run a command!
    '''
    log = logging.getLogger("%s.execute" % LOGROOT)
    stderr = ""
    stdout =""
    cmd = cmdline.split(" ")
    log.debug("cmd execute: %s" % str(cmd))
    handle = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while 1:
        time.sleep(0.1)
        handle.poll()
        response = handle.communicate()
        out = gatherRetval(response[0])
        try:
            err = gatherRetval(response[1])
        except AttributeError:
            err = ""
            pass
        stdout   += out
        stderr   += err
        _log.info(out)
        if len(err): log.debug('debug: %s' % err)
        if handle.returncode != None:
            break
        continue

    retval = "%s\n%s" % (stdout, stderr)
    retval = retval.strip()
    log.debug("cmd returns (%d): \n%s" % (handle.returncode, retval))
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


def InteractiveRun(cmd):
    '''
    run 'cmd' interactively, giving feedback as it happens
    '''
    log = logging.getLogger("%s.Interactive" % LOGROOT)
    _cmd_execute(cmd)
    return True

def LoggerRun(cmd):
    '''
    run 'cmd', log important messages
    '''
    _cmd_execute(cmd)
    return True

def TestRun(cmd):
    '''
    run 'cmd', log important messages
    '''
    log = logging.getLogger("%s.Test" % LOGROOT)
    message = "WOULD: %s" % cmd
    log.info(message)
    return True

def locateBtrfs():
    '''
    local all BTRFS filesystems
    '''
    log = logging.getLogger("%s.locatebtrfs" % LOGROOT)
    retval = []
    filesystems = {}
    
    contents = open("/proc/mounts", "r").read()
    for x in contents.split("\n"):
        if x.find(" btrfs ") < 0: continue
        log.debug("located: %s" % x)
        f = x.split(" ")
        if len(f) < 3: continue
        if f[2] != 'btrfs': continue
        if f[1] in retval: continue
        try:
            filesystems[f[0]].append(f[1])
            log.debug("set examination: %s" % f[1])
        except KeyError:
            filesystems[f[0]] = [ f[1], ]
            log.debug("Error Resolving Key: %s: %s" % (f[0],f[1]))
            pass
        continue

    retval = [ filesystems[x][0] for x in filesystems.keys() ]
    return retval

def Maintain(fs, run, scrub):
    '''
    execute maintenance steps for [fs]
    '''
    log = logging.getLogger("%s.Maintain" % LOGROOT)
    for x in range(2):
        scrubrun = _cmd_btrfsScrubStatus(fs)
        if ScrubIsRunning(scrubrun):
            log.error("Existing Scrub Running for %s" % fs)
            click.echo("Error: Existing Scrub Running on %s." % fs)
            return False
        elif _cmd_btrfsBalanceRetval(fs):
            log.error("Existing Balance Running for %s" % fs)
            click.echo("Error: Existing Balance Running on %s" % fs)
            return False
        continue
    
    ### Balance Metadata
    run("btrfs balance start -musage=0 -v %s" % fs)
    if ScrubIsRunning(_cmd_btrfsScrubStatus(fs)) or _cmd_btrfsBalanceRetval(fs):
        log.error("Existing Balance or Scrub running on %s." % fs)
        return False
    run("btrfs balance start -musage=20 -v %s" % fs)
    if ScrubIsRunning(_cmd_btrfsScrubStatus(fs)) or _cmd_btrfsBalanceRetval(fs):
        log.error("Existing Balance or Scrub running on %s." % fs)
        return False
    ### Balance Data
    run("btrfs balance start -dusage=0 -v %s" % fs)
    if ScrubIsRunning(_cmd_btrfsScrubStatus(fs)) or _cmd_btrfsBalanceRetval(fs):
        log.error("Existing Balance or Scrub running on %s." % fs)
        return False
    run("btrfs balance start -dusage=20 -v %s" % fs)
    if ScrubIsRunning(_cmd_btrfsScrubStatus(fs)) or _cmd_btrfsBalanceRetval(fs):
        log.error("Existing Balance or Scrub running on %s." % fs)
        return False
    ### Scrub disks
    if scrub:
        log.debug("spawn scrub instance for %s." % fs)
        run("ionice -c 3 nice -10 btrfs scrub start -Bd %s" % fs)
        log.debug("Scrub complete for %s." % fs)
        pass
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
def Main(ctx, silent, test, allfs, scrub, filesystems, debug):
    '''
    perform btrfs filesystem maintenace for one, many or [-a]ll filesystems.
    '''
    global DEBUG, _log
    DEBUG=debug

    _log = logging.getLogger(LOGROOT)
    _log.setLevel(logging.INFO)
    sysh = SysLogHandler(address="/dev/log")
    outh = logging.StreamHandler(sys.stdout)
    
    if debug:
        logfmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')    
        sysh.setLevel(logging.DEBUG)
        outh.setLevel(logging.DEBUG)
        click.echo("arg allfs: %s" % str(allfs))
        click.echo("arg debug: %s" % str(debug))
        click.echo("arg silent: %s"  % str(silent))
        click.echo("arg test: %s"  % str(test))
    else:
        logfmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        sysh.setLevel(logging.INFO)
        outh.setLevel(logging.INFO)
        
    sysh.setFormatter(logfmt)
    outh.setFormatter(logfmt)
    
    if len(filesystems) == 0 and not allfs:
        click.echo("You must either use '-a' or specify a filesystem.")
        click.echo("")
        click.echo(ctx.get_help())
        exit()
        
    if test:
        run = TestRun
        click.echo("Run is set to Test")
        _log.addHandler(sysh)
        _log.addHandler(outh)
    elif silent:
        run = LoggerRun
        _log.addHandler(sysh)
        click.echo("Run is set to Logger")
    else:
        run = InteractiveRun
        click.echo("Run is set to Interactive")
        _log.addHandler(sysh)
        _log.addHandler(outh)

    if allfs:
        filesystems = locateBtrfs()

    _log.debug("arg filesystems: %s" % str(filesystems))

    for fs in filesystems:
        Maintain(fs, run, scrub)
        continue
    
    return True

if __name__ == "__main__":
    sys.exit(Main())
