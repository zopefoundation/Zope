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

import thread
from ZServerPublisher import ZServerPublisher

class ZRendevous:
    """Worker thread pool

    For better or worse, we hide locking sementics from the worker
    threads.  The worker threads do no locking.
    """ 

    def __init__(self, n=1):
        sync = thread.allocate_lock()
        self._acquire = sync.acquire
        self._release = sync.release
        pool = []
        self._lists = (
            pool, # Collection of locks representing threads are not
                  # waiting for work to do
            [],   # Request queue
            [],   # Pool of locks representing threads that are
                  # waiting (ready) for work to do.
            )
        
        self._acquire() # callers will block
        try:
            while n > 0:
                l = thread.allocate_lock()
                l.acquire()
                pool.append(l)
                thread.start_new_thread(ZServerPublisher,
                                        (self.accept,))
                n = n-1
        finally:
            self._release() # let callers through now

    def accept(self):
        """Return a request from the request queue

        If no requests are in the request queue, then block until
        there is nonw.
        """
        self._acquire() # prevent other calls to protect data structures
        try:
            pool, requests, ready = self._lists
            while not requests:
                # There are no requests in the queue. Wait until there are.

                # This thread is waiting, to remove a lock from the collection
                # of locks corresponding to threads not waiting for work
                l = pool.pop()

                # And add it to the collection of locks representing threads
                # ready and waiting for work.
                ready.append(l)
                self._release() # allow other calls

                # Now try to acquire the lock. We will block until
                # someone calls handle to queue a request and releases the lock
                # which handle finds in the ready queue
                l.acquire()

                self._acquire() # prevent calls so we can update
                                # not waiting pool
                pool.append(l)

            # return the *first* request
            return requests.pop(0)

        finally:
            self._release() # allow calls

    def handle(self, name, request, response):
        """Queue a request for processing
        """
        self._acquire() # prevent other calls to protect data structs
        try:
            pool, requests, ready = self._lists
            # queue request
            requests.append((name, request, response))
            if ready:
                # If any threads are ready and waiting for work
                # then remove one of the locks from the ready pool
                # and release it, letting the waiting thread go forward
                # and consume the request
                ready.pop().release()

        finally:
            self._release()
