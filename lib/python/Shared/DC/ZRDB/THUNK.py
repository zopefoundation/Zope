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

import TM, ThreadLock
from TM import Surrogate
import transaction

thunk_lock=ThreadLock.allocate_lock()

class THUNKED_TM(TM.TM):
    """A big heavy hammer for handling non-thread safe DAs
    """

    def _register(self):
        if not self._registered:
            thunk_lock.acquire()
            try:
                transaction.get().register(Surrogate(self))
                self._begin()
            except:
                thunk_lock.release()
                raise
            else:
                self._registered=1

    def tpc_finish(self, *ignored):
        if self._registered:
            try: self._finish()
            finally:
                thunk_lock.release()
                self._registered=0

    def abort(self, *ignored):
        if self._registered:
            try: self._abort()
            finally:
                thunk_lock.release()
                self._registered=0
