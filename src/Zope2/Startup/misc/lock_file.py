##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""Utility function for file locking.

This module provides a platform-specific function which uses the
best-available strategy for locking a file object.
"""

try:
    import fcntl
except ImportError:
    # Try windows-specific code:
    try:
        # We expect this module to exist, but the LockFile function may not.
        from ZODB.winlock import LockFile
    except ImportError:
        # we don't understand any kind of locking, forget it
        def lock_file(file):
            pass
    else:
        # Windows
        def lock_file(file):
            un = file.fileno()
            LockFile(un, 0, 0, 1, 0) # just lock the first byte, who cares
else:
    # Unix-specific locking:
    def lock_file(file):
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
