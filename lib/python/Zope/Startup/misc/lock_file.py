##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
""" Utilities for file locking """
try:
    import fcntl
    def lock_file(file):
        un=file.fileno()
        fcntl.flock(un, fcntl.LOCK_EX | fcntl.LOCK_NB)
except:
    # Try windows-specific code:
    try:
        from ZODB.winlock import LockFile
        def lock_file(file):
            un=file.fileno()
            LockFile(un,0,0,1,0) # just lock the first byte, who cares
    except:
        # we don't understand any kind of locking, forget it
        def lock_file(file):
            pass
