BTRFSMAINT
==========

This is a quick project based upon Marc MERLIN's [`btrfscrub.sh`](http://marc.merlins.org/linux/scripts/btrfs-scrub).  Fedora 24 doesn't have `shlock` in the INN package, and I decided to reimplement the script in Python.

Installation
------------

Download the script, place in /usr/local/bin, setup a monthly cronjob to execute the script.

Compatibility
-------------

 - Python 2.6+
 - Python 3.0+
 - PyPy 5+

Library Dependencies
--------------------

 - [Docopt](http://docopt.org/)


Files
-----
```
├── btrfscrub.sh       # Reference Copy of Marc MERLIN's Script (Apache 2.0 License)
├── btrfsmaint.py      # btrfsmaint script
├── btrfstest.py       # function test script.
├── README.md          # This File
└── tests/             # Test output.
```
