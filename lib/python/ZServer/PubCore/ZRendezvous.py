##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import thread
from ZServerPublisher import ZServerPublisher

class ZRendevous:

    def __init__(self, n=1):
        sync=thread.allocate_lock()
        self._a=sync.acquire
        self._r=sync.release
        pool=[]
        self._lists=pool, [], []
        self._a()
        try:
            while n > 0:
                l=thread.allocate_lock()
                l.acquire()
                pool.append(l)
                thread.start_new_thread(ZServerPublisher,
                                        (self.accept,))
                n=n-1
        finally: self._r()

    def accept(self):
        self._a()
        try:
            pool, requests, ready = self._lists
            while not requests:
                l=pool[-1]
                del pool[-1]
                ready.append(l)
                self._r()
                l.acquire()
                self._a()
                pool.append(l)

            r=requests[0]
            del requests[0]
            return r
        finally: self._r()

    def handle(self, name, request, response):
        self._a()
        try:
            pool, requests, ready = self._lists
            requests.append((name, request, response))
            if ready:
                l=ready[-1]
                del ready[-1]
                l.release()
        finally: self._r()
