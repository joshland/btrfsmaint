#! /bin/bash

# By Marc MERLIN <marc_soft@merlins.org> 2014/03/20
# License: Apache-2.0

function checkBalance(){
		
		
		return 1
}

function checkScrub(){
		btrfs scrub status ${x} | grep -E "no.stats.available|and.finished.after" > /dev/null
		if [ $? ]; then
				echo 'Scrub running'
		else
				echo 'Scrub not running'
		fi
		
		return 1
}

which btrfs >/dev/null || exit 0

export PATH=/usr/local/bin:/sbin:$PATH

# bash shortcut for `basename $0`
PROG=${0##*/}
lock=/var/run/$PROG

if which on_ac_power >/dev/null 2>&1; then
    ON_BATTERY=0
    on_ac_power >/dev/null 2>&1 || ON_BATTERY=$?
    if [ "$ON_BATTERY" -eq 1 ]; then
        exit 0
    fi
fi

FILTER='(^Dumping|balancing, usage)'
test -n "$DEVS" || DEVS=$(grep '\<btrfs\>' /proc/mounts | awk '{ print $1 }' | sort -u)
for btrfs in $DEVS
do

		
    journalctl -xe -n 0 -f /var/log/syslog | grep "BTRFS: " | grep -Ev '(disk space caching is enabled|unlinked .* orphans|turning on discard|device label .* devid .* transid|enabling SSD mode|BTRFS: has skinny extents|BTRFS: device label)' &
    mountpoint="$(grep "$btrfs" /proc/mounts | awk '{ print $2 }' | sort | head -1)"
    logger -s "Quick Metadata and Data Balance of $mountpoint ($btrfs)" >&2
    # Even in 4.3 kernels, you can still get in places where balance
    # won't work (no place left, until you run a -m0 one first)
    btrfs balance start -musage=0 -v $mountpoint 2>&1 | grep -Ev "$FILTER"
    btrfs balance start -musage=20 -v $mountpoint 2>&1 | grep -Ev "$FILTER"
    # After metadata, let's do data:
    btrfs balance start -dusage=0 -v $mountpoint 2>&1 | grep -Ev "$FILTER"
    btrfs balance start -dusage=20 -v $mountpoint 2>&1 | grep -Ev "$FILTER"
    # And now we do scrub. Note that scrub can fail with "no space left
    # on device" if you're very out of balance.
    logger -s "Starting scrub of $mountpoint" >&2
    echo btrfs scrub start -Bd $mountpoint
    ionice -c 3 nice -10 btrfs scrub start -Bd $mountpoint
    pkill -f 'tail -n 0 -f /var/log/syslog'
    logger "Ended scrub of $mountpoint" >&2
done

0
