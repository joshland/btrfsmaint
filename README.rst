BTRFSMAINT
==========

This is a quick project based upon Marc MERLIN's
```btrfscrub.sh`` <http://marc.merlins.org/linux/scripts/btrfs-scrub>`__.
Fedora 24 doesn't have ``shlock`` in the INN package, and I decided to
reimplement the script in Python.

Installation
------------

``pip install btrfsmaint``

Usage
-----

Single Drive
^^^^^^^^^^^^

Run a quick maintenance without a scrub on /home.

::

    btrfsmaint --no-scrub /home

Run quick maintanance on all BTRFS volumes currently mounted.

::

    btrfsmaint --no-scrub -a

Run via crontab, all mounted BTRFS volumes with scrub.

::

      0  0  *  *  * root       /usr/bin/btrfsmaint -a

Compatibility
-------------

-  Python 2.6+
-  Python 3.0+
-  PyPy 5+

Library Dependencies
--------------------

-  `Click <http://click.pocoo.org>`__

TODO
----

-  Perhaps a mutex of some sort or locking like unto shlock
-  Make some default scripts - cron, systemd, etc.

Files
-----

::

    ├── btrfscrub.sh
    ├── btrfsmaint
    │   └── __init__.py    # btrfsmaint contents.
    ├── btrfstest.py       # function test script.
    ├── LICENSE            # Apache2.0 License stub
    ├── MANIFEST.in        # distribute package manifest.
    ├── README.md          # This File.
    ├── README.rst         # ReST-rendered version of the md.
    ├── requirements.txt   # pip requirements file.
    ├── script
    │   ├── mkdocs.py      # Publish README.md -> README.rst (required pypandoc, pandoc)
    │   └── runtest.sh     # Mutli-py version test script.
    ├── setup.cfg          # distribute packaging helper.
    ├── setup.py           # build script.
    ├── Copyright          # Copyright Statement
    └── tests/             # Test output.
