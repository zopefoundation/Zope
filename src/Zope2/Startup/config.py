##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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

TRUSTED_PROXIES = []

ZSERVER_CONNECTION_LIMIT = 1000
ZSERVER_ENABLE_MS_PUBLIC_HEADER = False
ZSERVER_EXIT_CODE = 0
ZSERVER_LARGE_FILE_THRESHOLD = 524288
ZSERVER_THREADS = 1


def setNumberOfThreads(n):
    """This function will self-destruct in 4 statements.
    """
    global ZSERVER_THREADS
    ZSERVER_THREADS = n
    global setNumberOfThreads
    del setNumberOfThreads
