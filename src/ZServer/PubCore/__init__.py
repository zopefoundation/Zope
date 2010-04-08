##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import ZRendezvous

_handle=None
_n=1

def handle(*args, **kw):
    global _handle

    if _handle is None: _handle=ZRendezvous.ZRendevous(_n).handle

    return apply(_handle, args, kw)

def setNumberOfThreads(n):
    """This function will self-destruct in 4 statements.
    """
    global _n
    _n=n
    global setNumberOfThreads
    del setNumberOfThreads
